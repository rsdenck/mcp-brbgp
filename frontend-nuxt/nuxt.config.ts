export default defineNuxtConfig({
  devtools: { enabled: true },
  
  modules: ['@nuxt/ui'],
  
  ui: {
    global: true,
    icons: ['heroicons', 'simple-icons'],
    primaryColor: 'blue'
  },
  
  app: {
    head: {
      title: 'Bradar - BGP Intelligence',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Global BGP Intelligence Platform' }
      ],
      link: [
        { rel: 'stylesheet', href: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css' }
      ]
    }
  },

  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8002/api'
    }
  },

  compatibilityDate: '2024-11-01'
})
