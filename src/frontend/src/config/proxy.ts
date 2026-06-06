const DEFAULT_API_PROXY_TARGET = "http://127.0.0.1:8010";

export function resolveApiProxyTarget(env: Record<string, string | undefined>): string {
  return env.VITE_API_PROXY_TARGET || DEFAULT_API_PROXY_TARGET;
}
