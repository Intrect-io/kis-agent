/**
 * kis-agent TypeScript Bridge — JSON subprocess communication
 *
 * This package exports all bridge types and utilities for communicating with
 * the Python kis-cli-bridge subprocess.
 */

export type {
  BridgeRequest,
  BridgeResponse,
  CommandArgs,
  ErrorPayload,
  SuccessPayload,
  BridgeResponseWithNotice,
} from './types';

export { BridgeError, isErrorResponse, isSuccessResponse } from './types';
