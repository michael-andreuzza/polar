/* tslint:disable */
/* eslint-disable */
/**
 * Polar API
 *  Welcome to the **Polar API** for [polar.sh](https://polar.sh).  This specification contains both the definitions of the Polar HTTP API and the Webhook API.  #### Authentication  Use a [Personal Access Token](https://polar.sh/settings) and send it in the `Authorization` header on the format `Bearer [YOUR_TOKEN]`.  #### Feedback  If you have any feedback or comments, reach out in the [Polar API-issue](https://github.com/polarsource/polar/issues/834), or reach out on the Polar Discord server.  We\'d love to see what you\'ve built with the API and to get your thoughts on how we can make the API better!  #### Connecting  The Polar API is online at `https://api.polar.sh`. 
 *
 * The version of the OpenAPI document: 0.1.0
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */


import * as runtime from '../runtime';
import type {
  HTTPValidationError,
  Interval,
  MetricsResponse,
  ProductPriceType,
} from '../models/index';

export interface MetricsApiGetMetricsRequest {
    startDate: string;
    endDate: string;
    interval: Interval;
    organizationId?: string;
    productId?: string;
    productPriceType?: ProductPriceType;
}

/**
 * 
 */
export class MetricsApi extends runtime.BaseAPI {

    /**
     * Get metrics about your orders and subscriptions.
     * Get Metrics
     */
    async getMetricsRaw(requestParameters: MetricsApiGetMetricsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<MetricsResponse>> {
        if (requestParameters['startDate'] == null) {
            throw new runtime.RequiredError(
                'startDate',
                'Required parameter "startDate" was null or undefined when calling getMetrics().'
            );
        }

        if (requestParameters['endDate'] == null) {
            throw new runtime.RequiredError(
                'endDate',
                'Required parameter "endDate" was null or undefined when calling getMetrics().'
            );
        }

        if (requestParameters['interval'] == null) {
            throw new runtime.RequiredError(
                'interval',
                'Required parameter "interval" was null or undefined when calling getMetrics().'
            );
        }

        const queryParameters: any = {};

        if (requestParameters['startDate'] != null) {
            queryParameters['start_date'] = requestParameters['startDate'];
        }

        if (requestParameters['endDate'] != null) {
            queryParameters['end_date'] = requestParameters['endDate'];
        }

        if (requestParameters['interval'] != null) {
            queryParameters['interval'] = requestParameters['interval'];
        }

        if (requestParameters['organizationId'] != null) {
            queryParameters['organization_id'] = requestParameters['organizationId'];
        }

        if (requestParameters['productId'] != null) {
            queryParameters['product_id'] = requestParameters['productId'];
        }

        if (requestParameters['productPriceType'] != null) {
            queryParameters['product_price_type'] = requestParameters['productPriceType'];
        }

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("HTTPBearer", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/metrics/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response);
    }

    /**
     * Get metrics about your orders and subscriptions.
     * Get Metrics
     */
    async getMetrics(requestParameters: MetricsApiGetMetricsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<MetricsResponse> {
        const response = await this.getMetricsRaw(requestParameters, initOverrides);
        return await response.value();
    }

}