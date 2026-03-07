<template>
  <div class="space-y-6">
    <!-- Header Card -->
    <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-sm text-gray-400">Autonomous System</p>
          <h1 class="text-4xl font-bold text-white mt-1">AS{{ asn }}</h1>
          <p class="text-xl text-emerald-400 mt-2">{{ asnData?.name || 'Unknown' }}</p>
          
          <div class="flex items-center gap-6 mt-4">
            <div class="flex items-center gap-2 text-gray-400">
              <UIcon name="i-heroicons-flag" class="w-5 h-5" />
              <span>{{ asnData?.country || 'XX' }}</span>
            </div>
            <div class="text-gray-400">
              <span>Total no país: {{ asnData?.country_total_asns?.toLocaleString() || '-' }}</span>
            </div>
          </div>
        </div>
        
        <NuxtLink to="/" class="text-gray-400 hover:text-white">
          <UIcon name="i-heroicons-x-mark" class="w-6 h-6" />
        </NuxtLink>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- IP Info -->
      <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 class="text-lg font-semibold mb-4">Informações de IP</h3>
        <div class="space-y-4">
          <div class="flex justify-between items-center py-3 border-b border-gray-800">
            <span class="text-gray-400">IP Início</span>
            <span class="font-mono text-emerald-400">{{ asnData?.ip_start || '-' }}</span>
          </div>
          <div class="flex justify-between items-center py-3 border-b border-gray-800">
            <span class="text-gray-400">IP Fim</span>
            <span class="font-mono text-emerald-400">{{ asnData?.ip_end || '-' }}</span>
          </div>
          <div class="flex justify-between items-center py-3">
            <span class="text-gray-400">Total IPs</span>
            <span class="text-white">~256 (/24)</span>
          </div>
        </div>
      </div>

      <!-- Similar ASNs -->
      <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 class="text-lg font-semibold mb-4">ASNs Similares</h3>
        <div class="space-y-2">
          <div 
            v-for="sim in asnData?.similar_asns" 
            :key="sim.asn"
            class="flex items-center justify-between p-3 bg-gray-800/50 rounded-xl hover:bg-gray-800 cursor-pointer"
            @click="navigateTo(`/asn/${sim.asn}`)"
          >
            <span class="font-mono text-emerald-400">AS{{ sim.asn }}</span>
            <span class="text-gray-400 text-sm truncate max-w-[200px]">{{ sim.name }}</span>
          </div>
          <div v-if="!asnData?.similar_asns?.length" class="text-gray-500 text-center py-4">
            Nenhum ASN similar encontrado
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex gap-4">
      <UButton color="emerald" icon="i-heroicons-arrow-left" @click="navigateTo('/')">
        Voltar ao Dashboard
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { getASN } = useApi()

const asn = computed(() => parseInt(route.params.id as string))
const asnData = ref<any>(null)

onMounted(async () => {
  if (asn.value) {
    asnData.value = await getASN(asn.value)
  }
})
</script>
