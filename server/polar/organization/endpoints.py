from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from polar.auth.dependencies import Auth, UserRequiredAuth
from polar.authz.service import AccessType, Authz
from polar.enums import Platforms
from polar.exceptions import ResourceNotFound, Unauthorized
from polar.integrations.github.badge import GithubBadge
from polar.kit.pagination import ListResource, Pagination
from polar.postgres import AsyncSession, get_db_session
from polar.repository.service import repository as repository_service
from polar.tags.api import Tags

from .schemas import (
    Organization as OrganizationSchema,
)
from .schemas import (
    OrganizationBadgeSettingsRead,
    OrganizationBadgeSettingsUpdate,
    OrganizationUpdate,
    RepositoryBadgeSettingsRead,
)
from .service import organization

log = structlog.get_logger()

router = APIRouter(tags=["organizations"])


@router.get(
    "/organizations",
    response_model=ListResource[OrganizationSchema],
    tags=[Tags.PUBLIC],
    description="List organizations that the authenticated user is a member of. Requires authentication.",  # noqa: E501
    summary="List organizations (Public API)",
    status_code=200,
)
async def list(
    auth: UserRequiredAuth,
    is_admin_only: bool = Query(
        default=True,
        description="Include only organizations that the user is an admin of.",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ListResource[OrganizationSchema]:
    orgs = await organization.list_all_orgs_by_user_id(
        session, auth.user.id, is_admin_only
    )

    return ListResource(
        items=[OrganizationSchema.from_db(o) for o in orgs],
        pagination=Pagination(total_count=len(orgs), max_page=1),
    )


@router.get(
    "/organizations/search",
    response_model=ListResource[OrganizationSchema],
    tags=[Tags.PUBLIC],
    description="Search organizations.",
    summary="Search organizations (Public API)",
    status_code=200,
)
async def search(
    platform: Platforms | None = None,
    organization_name: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ListResource[OrganizationSchema]:
    # Search by platform and organization name.
    # Currently the only way to search
    if platform and organization_name:
        org = await organization.get_by_name(session, platform, organization_name)
        if org:
            return ListResource(
                items=[OrganizationSchema.from_db(org)],
                pagination=Pagination(total_count=0, max_page=1),
            )

    # no org found
    return ListResource(
        items=[],
        pagination=Pagination(total_count=0, max_page=1),
    )


@router.get(
    "/organizations/lookup",
    response_model=OrganizationSchema,
    tags=[Tags.PUBLIC],
    description="Lookup organization. Like search but returns at only one organization.",  # noqa: E501
    summary="Lookup organization (Public API)",
    status_code=200,
    responses={404: {}},
)
async def lookup(
    platform: Platforms | None = None,
    organization_name: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSchema:
    # Search by platform and organization name.
    # Currently the only way to search
    if platform and organization_name:
        org = await organization.get_by_name(session, platform, organization_name)
        if org:
            return OrganizationSchema.from_db(org)

    raise HTTPException(
        status_code=404,
        detail="Organization not found ",
    )


@router.get(
    "/organizations/{id}",
    response_model=OrganizationSchema,
    tags=[Tags.PUBLIC],
    description="Get organization",
    status_code=200,
    summary="Get organization (Public API)",
    responses={404: {}},
)
async def get(
    id: UUID,
    auth: Auth = Depends(Auth.optional_user),
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSchema:
    org = await organization.get(session, id=id)

    if not org:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return OrganizationSchema.from_db(org)


@router.patch(
    "/organizations/{id}",
    response_model=OrganizationSchema,
    tags=[Tags.PUBLIC],
    description="Update organization",
    status_code=200,
    summary="Update an organization (Public API)",
    responses={404: {}},
)
async def update(
    id: UUID,
    update: OrganizationUpdate,
    auth: Auth = Depends(Auth.current_user),
    authz: Authz = Depends(Authz.authz),
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSchema:
    org = await organization.get(session, id=id)
    if not org:
        raise ResourceNotFound()

    if not await authz.can(auth.subject, AccessType.write, org):
        raise Unauthorized()

    org = await organization.update_settings(session, org, update)

    return OrganizationSchema.from_db(org)


#
# Internal APIs below
#


@router.get(
    "/organizations/{id}/badge_settings",
    response_model=OrganizationBadgeSettingsRead,
    summary="Get badge settings (Internal API)",
)
async def get_badge_settings(
    id: UUID,
    auth: UserRequiredAuth,
    authz: Authz = Depends(Authz.authz),
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationBadgeSettingsRead:
    org = await organization.get(session, id)
    if not org:
        raise ResourceNotFound()
    if not await authz.can(auth.subject, AccessType.write, org):
        raise Unauthorized()

    repositories = await repository_service.list_by(
        session, org_ids=[org.id], order_by_open_source=True
    )

    synced = await repository_service.get_repositories_synced_count(session, org)

    repos = []
    for repo in repositories:
        open_issues = repo.open_issues or 0
        synced_data = synced.get(
            repo.id,
            {
                "synced_issues": 0,
                "auto_embedded_issues": 0,
                "label_embedded_issues": 0,
                "pull_requests": 0,
            },
        )
        synced_issues = synced_data["synced_issues"]
        if synced_issues > open_issues:
            open_issues = synced_issues

        is_sync_completed = synced_issues == open_issues

        repos.append(
            RepositoryBadgeSettingsRead(
                id=repo.id,
                avatar_url=org.avatar_url,
                badge_auto_embed=repo.pledge_badge_auto_embed,
                badge_label=repo.pledge_badge_label,
                name=repo.name,
                synced_issues=synced_issues,
                auto_embedded_issues=synced_data["auto_embedded_issues"],
                label_embedded_issues=synced_data["label_embedded_issues"],
                pull_requests=synced_data["pull_requests"],
                open_issues=open_issues,
                is_private=repo.is_private,
                is_sync_completed=is_sync_completed,
            )
        )

    message = org.default_badge_custom_content
    if not message:
        message = GithubBadge.generate_default_promotion_message(org)

    return OrganizationBadgeSettingsRead(
        show_amount=org.pledge_badge_show_amount,
        minimum_amount=org.pledge_minimum_amount,
        message=message,
        repositories=repos,
    )


@router.post(
    "/organizations/{id}/badge_settings",
    response_model=OrganizationSchema,
    tags=[Tags.INTERNAL],
    summary="Update badge settings (Internal API)",
)
async def update_badge_settings(
    id: UUID,
    settings: OrganizationBadgeSettingsUpdate,
    auth: UserRequiredAuth,
    authz: Authz = Depends(Authz.authz),
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSchema:
    org = await organization.get(session, id)
    if not org:
        raise ResourceNotFound()
    if not await authz.can(auth.subject, AccessType.write, org):
        raise Unauthorized()

    # convert payload into OrganizationUpdate format
    org_update = OrganizationUpdate()
    if settings.show_amount is not None:
        org_update.pledge_badge_show_amount = settings.show_amount

    if settings.minimum_amount is not None:
        org_update.pledge_minimum_amount = settings.minimum_amount

    if settings.message:
        org_update.set_default_badge_custom_content = True
        org_update.default_badge_custom_content = settings.message

    await organization.update_settings(session, org, org_update)

    # save repositories settings
    repositories = await repository_service.list_by_ids_and_organization(
        session, [r.id for r in settings.repositories], org.id
    )
    for repository_settings in settings.repositories:
        if repository := next(
            (r for r in repositories if r.id == repository_settings.id), None
        ):
            await repository_service.update_badge_settings(
                session, org, repository, repository_settings
            )

    log.info(
        "organization.update_badge_settings",
        organization_id=org.id,
        settings=settings.dict(),
    )

    # get for return
    org = await organization.get(session, id)
    if not org:
        raise ResourceNotFound()
    return OrganizationSchema.from_db(org)
