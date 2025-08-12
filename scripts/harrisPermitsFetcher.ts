#!/usr/bin/env tsx

/**
 * Harris County Issued Permits Fetcher
 * Implements the exact specification for fetchHarrisIssuedPermits function
 */

import axios from 'axios';

// Default Harris County Issued Permits FeatureServer URL
const DEFAULT_HC_URL = 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0';

interface PermitRecord {
  event_id: string;
  permit_number: string | null;
  permit_name: string | null;
  app_type: string | null;
  issue_date_iso: string | null;
  full_address: string | null;
  street_number: string | null;
  street_name: string | null;
  status: string | null;
  project_number: string | null;
  raw: Record<string, any>;
}

interface ArcGISFeature {
  attributes: Record<string, any>;
}

interface ArcGISResponse {
  features: ArcGISFeature[];
  exceededTransferLimit?: boolean;
  count?: number;
}

/**
 * Sleep for a specified number of milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Generate random jitter for retry delays
 */
function getJitterDelay(baseDelay: number): number {
  return baseDelay + Math.random() * 1000; // Add up to 1 second of jitter
}

/**
 * Fetches Harris County issued permits since a given timestamp
 * 
 * @param sinceMs - Timestamp in milliseconds since epoch
 * @returns Array of permit records
 */
export async function fetchHarrisIssuedPermits(sinceMs: number): Promise<PermitRecord[]> {
  const baseUrl = process.env.HC_ISSUED_PERMITS_URL || DEFAULT_HC_URL;
  const whereClause = `ISSUEDDATE > ${sinceMs}`;
  
  // Step 1: Check count first
  const countUrl = `${baseUrl}/query?where=${encodeURIComponent(whereClause)}&returnCountOnly=true&f=json`;
  
  let count: number;
  let retryCount = 0;
  const maxRetries = 5;
  
  // Check count with retry logic
  while (retryCount < maxRetries) {
    try {
      console.log(`Checking count (attempt ${retryCount + 1}/${maxRetries}): ${countUrl}`);
      
      const countResponse = await axios.get(countUrl, {
        timeout: 30000,
        headers: {
          'User-Agent': 'Home-Services-Lead-Generation/1.0'
        }
      });
      
      if (countResponse.status !== 200) {
        throw new Error(`HTTP ${countResponse.status}: ${countResponse.statusText}`);
      }
      
      const countData = countResponse.data;
      count = countData.count;
      
      if (count === 0) {
        throw new Error(`No permits found since ${new Date(sinceMs).toISOString()}. Full query URL: ${countUrl}`);
      }
      
      console.log(`Found ${count} permits to fetch`);
      break;
      
    } catch (error: any) {
      const isRetryableError = (
        error.response?.status === 429 ||
        (error.response?.status >= 500 && error.response?.status < 600) ||
        error.code === 'ECONNRESET' ||
        error.code === 'ETIMEDOUT'
      );
      
      if (retryCount < maxRetries - 1 && isRetryableError) {
        retryCount++;
        const delay = getJitterDelay(Math.pow(2, retryCount) * 1000); // Exponential backoff with jitter
        console.warn(`Count check failed (attempt ${retryCount}/${maxRetries}), retrying in ${Math.round(delay)}ms:`, error.message);
        await sleep(delay);
        continue;
      }
      
      throw error;
    }
  }
  
  // Step 2: Fetch data in 2000-row chunks
  const permits: PermitRecord[] = [];
  let offset = 0;
  const pageSize = 2000;
  let totalFetched = 0;
  
  while (offset < count!) {
    retryCount = 0;
    
    while (retryCount < maxRetries) {
      try {
        const queryParams = new URLSearchParams({
          where: whereClause,
          outFields: '*',
          f: 'json',
          resultOffset: offset.toString(),
          resultRecordCount: pageSize.toString(),
          orderByFields: 'ISSUEDDATE DESC'
        });
        
        const url = `${baseUrl}/query?${queryParams}`;
        console.log(`Fetching page ${Math.floor(offset / pageSize) + 1} (offset: ${offset}, count: ${Math.min(pageSize, count! - offset)})`);
        
        const response = await axios.get(url, {
          timeout: 30000,
          headers: {
            'User-Agent': 'Home-Services-Lead-Generation/1.0'
          }
        });
        
        if (response.status !== 200) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = response.data as ArcGISResponse;
        
        if (!data.features || !Array.isArray(data.features)) {
          throw new Error('Invalid response format from ArcGIS server');
        }
        
        // Map fields to our schema
        for (const feature of data.features) {
          const attrs = feature.attributes;
          
          const permit: PermitRecord = {
          if (!attrs.EVENTID && !attrs.OBJECTID) {
            throw new Error('Permit record missing both EVENTID and OBJECTID; cannot assign event_id.');
          }
          const permit: PermitRecord = {
            event_id: attrs.EVENTID?.toString() || attrs.OBJECTID?.toString(),
            permit_number: attrs.PERMITNUMBER || null,
            permit_name: attrs.PERMITNAME || attrs.PROJECTNAME || null,
            app_type: attrs.APPTYPE || null,
            issue_date_iso: attrs.ISSUEDDATE ? new Date(attrs.ISSUEDDATE).toISOString() : null,
            full_address: attrs.FULLADDRESS || null,
            street_number: attrs.STREETNUMBER || null,
            street_name: attrs.STREETNAME || null,
            status: attrs.STATUS || null,
            project_number: attrs.PROJECTNUMBER || null,
            raw: attrs
          };
          
          permits.push(permit);
        }
        
        totalFetched += data.features.length;
        console.log(`Fetched ${data.features.length} permits in this batch (total: ${totalFetched})`);
        
        // Break if we got fewer results than expected (end of data)
        if (data.features.length < pageSize) {
          break;
        }
        
        offset += pageSize;
        break;
        
      } catch (error: any) {
        const isRetryableError = (
          error.response?.status === 429 ||
          (error.response?.status >= 500 && error.response?.status < 600) ||
          error.code === 'ECONNRESET' ||
          error.code === 'ETIMEDOUT'
        );
        
        if (retryCount < maxRetries - 1 && isRetryableError) {
          retryCount++;
          const delay = getJitterDelay(Math.pow(2, retryCount) * 1000); // Exponential backoff with jitter
          console.warn(`Page fetch failed (attempt ${retryCount}/${maxRetries}) for offset ${offset}, retrying in ${Math.round(delay)}ms:`, error.message);
          await sleep(delay);
          continue;
        }
        
        throw error;
      }
    }
  }
  
  console.log(`✅ Successfully fetched ${totalFetched} total permits`);
  return permits;
}