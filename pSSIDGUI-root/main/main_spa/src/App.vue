<template>

  <div>
    <div
      style="position: absolute; left: 2em; top: 2em"
      v-if="directory.path"
    >
      Selected Inventory: {{ directory.path }}
    </div>
    <div class="col text-center" style="font-size: 50px">pSSID Web GUI</div>
    <hr />
    <div id="app">
      <div id="loader" style="display: block" ref="loader"></div>
      <div ref="tabs">
        <!-- navbar -->
        <b-tabs fill>
          <b-tab
            :title="pluralize(tab)"
            :disabled="tab != 'Inventory' && directory.path == undefined"
            v-for="(tab, index) in tablist"
            :key="tab"
            v-on:click="tabHandler(index)"
            :class="{ active: index == activeIndex }"
          >
            <div v-if="index == 0">
              <node-vue
                v-model="directories"
                v-if="activeIndex == 0"
                :listData="['name']"
                filename="directory"
                @refresh="refresh"
                :tab="tab"
                @nodePicked="directoryHandler"
                :initactive="directory.id"
              >
              </node-vue>
            </div>
            <div v-if="index == 1">
              <node-vue
                v-model="hosts"
                v-if="activeIndex == 1"
                :listData="['name', 'ip']"
                :filename="'host'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
              <!-- dear future me the v-if activeindex stuff is necessary because the data is async  -->
              <!-- itll render the component first before the host data arrives so itll be empty -->
            </div>
            <div v-if="index == 2">
              <node-vue
                v-model="groups"
                v-if="activeIndex == 2"
                :listData="['name']"
                :filename="'group'"
                @refresh="refresh"
                :extraData="[hosts]"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 3">
              <node-vue
                v-model="schedules"
                v-if="activeIndex == 3"
                :listData="['name', 'repeatstring']"
                :filename="'schedule'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 4">
              <node-vue
                v-model="bssid_channels"
                v-if="activeIndex == 4"
                :listData="['name']"
                :filename="'bssid_channel'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 5">
              <node-vue
                v-model="ssid_profiles"
                v-if="activeIndex == 5"
                :listData="['name']"
                :filename="'ssid_profile'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 6">
              <node-vue
                v-model="ssid_groups"
                v-if="activeIndex == 6"
                :listData="['name']"
                :filename="'ssid_group'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 7">
              <node-vue
                v-model="network_interfaces"
                v-if="activeIndex == 7"
                :listData="['name', 'interface']"
                :filename="'network_interface'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 8">
              <node-vue
                v-model="bssid_scans"
                v-if="activeIndex == 8"
                :listData="['name']"
                :filename="'bssid_scan'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 9">
              <node-vue
                v-model="archivers"
                v-if="activeIndex == 9"
                :listData="['name']"
                :filename="'archiver'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 10">
              <node-vue
                v-model="tests"
                v-if="activeIndex == 10"
                :listData="['name']"
                :filename="'test'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
            <div v-if="index == 11">
              <node-vue
                v-model="tasks"
                v-if="activeIndex == 11"
                :listData="['name']"
                :filename="'task'"
                @refresh="refresh"
                :tab="tab"
              ></node-vue>
            </div>
          </b-tab>
        </b-tabs>
      </div>
    </div>
  </div>
</template>
  
<script lang="ts">
import nodeVue from "./components/nodeVue.vue";
import Vue from "vue";
import axios from "axios";
import VueAxios from "vue-axios";
import Cookies from 'js-cookie'
import VuePluralize from 'vue-pluralize'
 
Vue.use(VuePluralize)
Vue.use(VueAxios, axios);

import Darkmode from "darkmode-js";

const options = {
  label: "🌓",
  autoMatchOsTheme: false, // default: true
};

const darkmode = new Darkmode(options);
darkmode.showWidget();


export default Vue.extend({
  name: "App",
  delimiters: ["[[", "]]"],
  data: function () {
    return {
      tablist: [
        "Inventory",
        "Host",
        "Group",
        "Schedule",
        "BSSID Channel",
        "SSID Profile",
        "SSID Group",
        "Network Interface",
        "BSSID Scan",
        "Archiver",
        "Test",
        "Task",
      ],
      activeIndex: 0,
      hosts: [],
      groups: [],
      schedules: [],
      bssid_channels: [],
      ssid_profiles: [],
      ssid_groups: [],
      network_interfaces: [],
      bssid_scans: [],
      archivers: [],
      tests: [],
      tasks: [],
      directories: [],
      directory: {path: null, id: null},
      testnames: [],
      archivernames: [],
    };
  },
  methods: {
    tabHandler(index) {
      this.activeIndex = index;
    },
    refresh(directory = this.directory.path) {
      this.$refs.tabs.style.display = "none";
      this.$refs.loader.style.display = "block";
      Vue.axios
        .get("/init/", {
          params: {
            directory: directory,
          },
        })
        .then((response) => {
          console.log(response.data);
          const csrftoken = response.data["token"];
          Cookies.set("csrftoken", csrftoken);
          Vue.axios.defaults.headers.common['X-CSRFTOKEN'] = csrftoken;
          for (var key in response.data) {
            if (key != "token"){
              this[key] = response.data[key];
            }
          }
          // convert from key: value to key: key value: value

          for (let i = 0; i < this.hosts.length; i++) {
            for (let j = 0; j < this.hosts[i].meta.length; j++) {
              this.hosts[i].meta[j] = {
                key: Object.keys(this.hosts[i].meta[j])[0],
                value: Object.values(this.hosts[i].meta[j])[0],
              };
            }
          }

          for (let i = 0; i < this.groups.length; i++) {
            for (let j = 0; j < this.groups[i].meta.length; j++) {
              this.groups[i].meta[j] = {
                key: Object.keys(this.groups[i].meta[j])[0],
                value: Object.values(this.groups[i].meta[j])[0],
              };
            }
          }
          for (let i = 0; i < this.tests.length; i++) {

            
            for (let j = 0; j < this.tests[i].meta.length; j++) {
              this.tests[i].meta[j] = {
                key: Object.keys(this.tests[i].meta[j])[0],
                value: Object.values(this.tests[i].meta[j])[0],
              };
            }
          }

          for (let i = 0; i < this.archivers.length; i++) {
            for (let j = 0; j < this.archivers[i].meta.length; j++) {
              this.archivers[i].meta[j] = {
                key: Object.keys(this.archivers[i].meta[j])[0],
                value: Object.values(this.archivers[i].meta[j])[0],
              };
            }
          }
          this.$refs.tabs.style.display = "block";
          this.$refs.loader.style.display = "none";
        });
    },
    directoryHandler(node) {
      this.directory = node;
      this.refresh(node.path);
    },
    pluralize(word : String): String{
      return this.$pluralize(word)
    }
  },

  mounted() {
    // display loader and hide tabs while loading
    this.$refs.tabs.style.display = "none";
    this.$refs.loader.style.display = "block";
    Vue.axios.get("/init/").then((response) => {
      console.log(response.data);
      const csrftoken = response.data["token"];
      Cookies.set("csrftoken", csrftoken);
      Vue.axios.defaults.headers.common['X-CSRFTOKEN'] = csrftoken;
      for (var key in response.data) {
        if (key != "token"){
          this[key] = response.data[key];
        }
      }

      

      // convert from key: value to key: key value: value

      for (let i = 0; i < this.hosts.length; i++) {
        for (let j = 0; j < this.hosts[i].meta.length; j++) {
          this.hosts[i].meta[j] = {
            key: Object.keys(this.hosts[i].meta[j])[0],
            value: Object.values(this.hosts[i].meta[j])[0],
          };
        }
      }

      for (let i = 0; i < this.groups.length; i++) {
        for (let j = 0; j < this.groups[i].meta.length; j++) {
          this.groups[i].meta[j] = {
            key: Object.keys(this.groups[i].meta[j])[0],
            value: Object.values(this.groups[i].meta[j])[0],
          };
        }
      }

      for (let i = 0; i < this.tests.length; i++) {
        for (let j = 0; j < this.tests[i].meta.length; j++) {
          this.tests[i].meta[j] = {
            key: Object.keys(this.tests[i].meta[j])[0],
            value: Object.values(this.tests[i].meta[j])[0],
          };
        }
      }

      for (let i = 0; i < this.archivers.length; i++) {
        for (let j = 0; j < this.archivers[i].meta.length; j++) {
          this.archivers[i].meta[j] = {
            key: Object.keys(this.archivers[i].meta[j])[0],
            value: Object.values(this.archivers[i].meta[j])[0],
          };
        }
      }
      this.$refs.tabs.style.display = "block";
      this.$refs.loader.style.display = "none";

    });
  },
  components: {
    "node-vue": nodeVue,
  },
  watch: {
    hosts: {
      // when a new host is created add it to the all group
      handler(newval, oldval) {
        if (newval.length == oldval.length + 1) {
          for (var item of this.groups) {
            if (item.name == "all") {
              item.nodes.push(newval[newval.length - 1].ip);
              return;
            }
          }
        }
      },
      deep: true,
    },
  },
  created() {
    this.$pluralize.addIrregularRule("Main", "Main");
  }
});
</script>

<style>
@import "./assets/style.css";
</style>