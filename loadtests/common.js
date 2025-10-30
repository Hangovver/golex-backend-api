
import http from 'k6/http';
import { sleep, check } from 'k6';

export const BASE = __ENV.GOLEX_API || 'http://localhost:8000';
export const HEADERS = { 'Accept': 'application/json' };
export const options = {
  vus: Number(__ENV.VUS || 20),
  duration: __ENV.DURATION || '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    checks: ['rate>0.99'],
  },
};
