export const useApi = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBase as string

  const getStats = async () => {
    return await $fetch(`${baseUrl}/stats`)
  }

  const search = async (q: string, limit = 20) => {
    return await $fetch(`${baseUrl}/search?q=${encodeURIComponent(q)}&limit=${limit}`)
  }

  const getASN = async (asn: number) => {
    return await $fetch(`${baseUrl}/asn/${asn}`)
  }

  const getOperators = async (limit = 50) => {
    return await $fetch(`${baseUrl}/operators?limit=${limit}`)
  }

  const getCountries = async () => {
    return await $fetch(`${baseUrl}/countries`)
  }

  const getTraffic = async () => {
    return await $fetch(`${baseUrl}/traffic`)
  }

  const getGlobalOperators = async () => {
    return await $fetch(`${baseUrl}/global/operators`)
  }

  return {
    getStats,
    search,
    getASN,
    getOperators,
    getCountries,
    getTraffic,
    getGlobalOperators
  }
}
