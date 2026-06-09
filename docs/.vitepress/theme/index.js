import DefaultTheme from 'vitepress/theme'
import PaperBrowser from './components/PaperBrowser.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('PaperBrowser', PaperBrowser)
  },
}
