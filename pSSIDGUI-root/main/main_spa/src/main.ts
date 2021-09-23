import Vue from 'vue'
import App from './App.vue'

import { BootstrapVue } from 'bootstrap-vue'



import axios from 'axios'
import VueAxios from 'vue-axios'
import Cookies from 'js-cookie'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

const csrftoken = Cookies.get('csrftoken');
axios.defaults.headers.common['X-CSRFTOKEN'] = csrftoken;

Vue.config.devtools = true;

Vue.use(BootstrapVue)
Vue.use(VueAxios, axios)

import { extend, ValidationProvider } from 'vee-validate'
import * as rules from 'vee-validate/dist/rules'
import { messages } from 'vee-validate/dist/locale/en.json'

Vue.config.productionTip = false
Vue.component('ValidationProvider', ValidationProvider)


Object.keys(rules).forEach((rule) => {
    extend(rule, {
      ...rules[rule],
      message: messages[rule]
    })
  })

const mainVue = new Vue({
    render: h => h(App),
}).$mount('#app');

