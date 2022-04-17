import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import installElementPlus from './plugins/element'
import {Document,Expand,UploadFilled,List,DocumentAdd} from '@element-plus/icons-vue'
import axios from 'axios'


const app = createApp(App)
app.config.globalProperties.$axios = axios
installElementPlus(app)
app.component('document',Document)
   .component('expand',Expand)
   .component('upload-filled',UploadFilled)
   .component('list',List)
   .component('document-add',DocumentAdd)
app.use(store).use(router).mount('#app')

