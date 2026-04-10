/**
 * Next.js Instrumentation Hook
 * 
 * Node.js v25에서 localStorage가 글로벌로 노출되지만 
 * --localstorage-file 없이는 메서드가 동작하지 않는 문제를 해결.
 * 서버 사이드에서만 Map 기반의 간이 localStorage를 주입한다.
 */
export async function register() {
  if (typeof window === 'undefined') {
    // 서버 환경에서만 폴리필 적용
    const storage = new Map<string, string>()

    ;(globalThis as any).localStorage = {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => storage.set(key, String(value)),
      removeItem: (key: string) => storage.delete(key),
      clear: () => storage.clear(),
      get length() { return storage.size },
      key: (index: number) => [...storage.keys()][index] ?? null,
    }
  }
}
