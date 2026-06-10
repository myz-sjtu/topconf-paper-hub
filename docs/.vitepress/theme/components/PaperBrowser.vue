<script setup>
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps({
  conference: {
    type: String,
    default: '',
  },
  year: {
    type: [String, Number],
    default: '',
  },
  domain: {
    type: String,
    default: '',
  },
})

const papers = ref([])
const loading = ref(true)
const error = ref('')
const query = ref('')
const conference = ref(props.conference)
const year = ref(props.year ? String(props.year) : '')
const domain = ref(props.domain)
const visibleCount = ref(80)

const domainLabels = {
  network: 'Network',
  architecture: 'Architecture',
  ai: 'AI',
}

onMounted(async () => {
  try {
    const response = await fetch(withBase('/data/papers.json'))
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    papers.value = await response.json()
  } catch (event) {
    error.value = 'No exported paper data found yet.'
  } finally {
    loading.value = false
  }
})

const sortedPapers = computed(() =>
  [...papers.value].sort((left, right) => {
    if (right.year !== left.year) return right.year - left.year
    if (left.conference !== right.conference) return left.conference.localeCompare(right.conference)
    return left.title.localeCompare(right.title)
  }),
)

const conferences = computed(() => unique(sortedPapers.value.map((paper) => paper.conference)))
const years = computed(() => unique(sortedPapers.value.map((paper) => String(paper.year))).sort().reverse())
const domains = computed(() => unique(sortedPapers.value.map((paper) => paper.domain)))

const filteredPapers = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return sortedPapers.value.filter((paper) => {
    const text = [
      paper.title,
      paper.abstract,
      paper.conference,
      paper.domain,
      ...(paper.tags || []),
      ...(paper.authors || []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return (
      (!needle || text.includes(needle)) &&
      (!conference.value || paper.conference === conference.value) &&
      (!year.value || String(paper.year) === year.value) &&
      (!domain.value || paper.domain === domain.value)
    )
  })
})

const visiblePapers = computed(() => filteredPapers.value.slice(0, visibleCount.value))

function unique(items) {
  return [...new Set(items.filter(Boolean))].sort((left, right) => left.localeCompare(right))
}

function resetFilters() {
  query.value = ''
  conference.value = props.conference
  year.value = props.year ? String(props.year) : ''
  domain.value = props.domain
  visibleCount.value = 80
}
</script>

<template>
  <section class="paper-browser" aria-label="Paper browser">
    <div class="paper-browser__toolbar">
      <label class="paper-browser__search">
        <span>Search</span>
        <input v-model="query" type="search" placeholder="title, author, abstract, tag" />
      </label>

      <label>
        <span>Conference</span>
        <select v-model="conference">
          <option value="">All</option>
          <option v-for="item in conferences" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>

      <label>
        <span>Year</span>
        <select v-model="year">
          <option value="">All</option>
          <option v-for="item in years" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>

      <label>
        <span>Category</span>
        <select v-model="domain">
          <option value="">All</option>
          <option v-for="item in domains" :key="item" :value="item">
            {{ domainLabels[item] || item }}
          </option>
        </select>
      </label>

      <button type="button" @click="resetFilters">Reset</button>
    </div>

    <div class="paper-browser__meta">
      <strong>{{ filteredPapers.length }}</strong>
      <span>matched papers</span>
      <span v-if="papers.length">from {{ papers.length }} collected records</span>
    </div>

    <p v-if="loading" class="paper-browser__state">Loading papers...</p>
    <p v-else-if="error" class="paper-browser__state">{{ error }}</p>

    <div v-else class="paper-list">
      <article v-for="paper in visiblePapers" :key="paper.id" class="paper-card">
        <div class="paper-card__top">
          <span class="paper-card__venue">{{ paper.conference }} {{ paper.year }}</span>
          <span class="paper-card__domain">{{ domainLabels[paper.domain] || paper.domain }}</span>
        </div>

        <h2>
          <a v-if="paper.paper_url || paper.pdf_url" :href="paper.paper_url || paper.pdf_url" target="_blank" rel="noreferrer">
            {{ paper.title }}
          </a>
          <span v-else>{{ paper.title }}</span>
        </h2>

        <p class="paper-card__authors">{{ (paper.authors || []).slice(0, 10).join(', ') }}</p>
        <p class="paper-card__abstract">{{ paper.abstract || 'No abstract collected yet.' }}</p>

        <div class="paper-card__footer">
          <span v-for="tag in paper.tags || []" :key="tag" class="paper-card__tag">{{ tag }}</span>
          <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" rel="noreferrer">PDF</a>
          <a v-if="paper.doi" :href="`https://doi.org/${paper.doi}`" target="_blank" rel="noreferrer">DOI</a>
        </div>
      </article>

      <button
        v-if="visiblePapers.length < filteredPapers.length"
        type="button"
        class="paper-browser__more"
        @click="visibleCount += 80"
      >
        Show more
      </button>
    </div>
  </section>
</template>

<style scoped>
.paper-browser {
  margin: 24px 0 36px;
}

.paper-browser__toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(128px, 1fr)) auto;
  gap: 12px;
  align-items: end;
  padding: 14px;
  border: 1px solid var(--paper-border);
  border-radius: 8px;
  background: var(--paper-surface);
}

.paper-browser__toolbar label {
  display: grid;
  gap: 5px;
  color: var(--paper-muted);
  font-size: 12px;
  font-weight: 650;
}

.paper-browser__toolbar input,
.paper-browser__toolbar select {
  width: 100%;
  height: 36px;
  border: 1px solid var(--paper-border);
  border-radius: 6px;
  padding: 0 10px;
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg);
}

.paper-browser__toolbar button,
.paper-browser__more {
  height: 36px;
  border: 1px solid var(--paper-border);
  border-radius: 6px;
  padding: 0 14px;
  color: var(--vp-c-text-1);
  background: var(--paper-accent-soft);
  cursor: pointer;
}

.paper-browser__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: baseline;
  margin: 14px 0;
  color: var(--paper-muted);
}

.paper-browser__meta strong {
  color: var(--paper-accent);
  font-size: 24px;
}

.paper-browser__state {
  padding: 18px;
  border: 1px solid var(--paper-border);
  border-radius: 8px;
}

.paper-list {
  display: grid;
  gap: 12px;
}

.paper-card {
  padding: 16px;
  border: 1px solid var(--paper-border);
  border-radius: 8px;
  background: var(--paper-surface);
}

.paper-card__top,
.paper-card__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.paper-card__venue,
.paper-card__domain,
.paper-card__tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 700;
}

.paper-card__venue {
  color: var(--paper-cool);
  background: color-mix(in srgb, var(--paper-cool), transparent 88%);
}

.paper-card__domain {
  color: var(--paper-warm);
  background: color-mix(in srgb, var(--paper-warm), transparent 88%);
}

.paper-card__tag {
  color: var(--paper-accent);
  background: var(--paper-accent-soft);
}

.paper-card h2 {
  margin: 10px 0 6px;
  font-size: 19px;
  line-height: 1.35;
}

.paper-card__authors {
  margin: 0 0 8px;
  color: var(--paper-muted);
  font-size: 13px;
}

.paper-card__abstract {
  margin: 0 0 12px;
  line-height: 1.6;
}

.paper-card__footer a {
  font-size: 13px;
  font-weight: 700;
}

.paper-browser__more {
  justify-self: center;
  margin-top: 8px;
}

@media (max-width: 860px) {
  .paper-browser__toolbar {
    grid-template-columns: 1fr 1fr;
  }

  .paper-browser__search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 560px) {
  .paper-browser__toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
