import { createApp } from 'vue'
import './style.css'
import './styles/animations.css'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'

const app = createApp(App)
const pinia = createPinia()

// 重要：必须先安装 pinia，再安装 router
// 因为路由守卫中需要使用 store
app.use(pinia)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
