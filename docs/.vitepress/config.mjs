import { defineConfig } from 'vitepress'
import { generatedSidebar } from './generated-sidebar.mjs'

export default defineConfig({
  title: 'TopConf Paper Hub',
  description: 'Static top-conference paper index generated from collected metadata.',
  base: process.env.VITEPRESS_BASE || '/',
  cleanUrls: true,
  lastUpdated: true,
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Conferences', link: '/conferences/' },
      { text: 'Years', link: '/years/' },
      { text: 'Domains', link: '/domains/' },
      { text: 'Data', link: '/data/papers.json' },
    ],
    sidebar: {
      ...generatedSidebar,
      '/': [
        { text: 'Home', link: '/' },
        { text: 'Conferences', link: '/conferences/' },
        { text: 'Years', link: '/years/' },
        { text: 'Domains', link: '/domains/' },
        { text: 'Architecture', link: '/architecture' },
        { text: 'API', link: '/api' },
      ],
    },
    search: {
      provider: 'local',
    },
    outline: {
      level: [2, 3],
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/' },
    ],
  },
})

