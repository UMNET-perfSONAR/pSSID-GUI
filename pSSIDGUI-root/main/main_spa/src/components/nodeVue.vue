<template>
  <div ref="root">
    <div id="node-list" class="border rounded">
      <h2 class="text-center" id="node-title">{{ pluralize(tab) }}</h2>
      <div class="form-group" id="node-search-container">
        <input
          v-model="nodeSearch"
          type="text"
          id="node-search"
          class="search form-control"
          placeholder="Search..."
        />
      </div>
      <div class="node-button-container">
        <button
          id="add-node-button"
          class="btn btn-success"
          style="display: inline-block"
          v-on:click="addNode"
        >
          Add {{ tab }}
        </button>

        <button
          id="refresh-button"
          class="btn btn-primary"
          style="display: inline-block"
          v-on:click="refresh_nodes()"
        >
          <span
            class="material-icons"
            style="font-size: 18px; vertical-align: -3px"
            >refresh</span
          >
        </button>
      </div>
      <div id="inner-node-list-container">
        <div class="list list-group" id="inner-node-list" role="tablist">
          <div
            v-bind:key="index"
            v-for="(node, index) in filtered_node_list"
            :id="'node-tab-' + index.toString()"
            class="node list-group-item list-group-item-action"
            v-bind:class="{ active: active_nodes.includes(index) }"
            data-bs-toggle="list"
            role="tab"
            style="display: block; cursor: pointer"
            @click="nodeButtonHandler(index)"
          >
            <span v-if="filename == 'directory'" class="name">{{
              node[listData[0]]
            }}</span>
            <span v-else class="name">{{ node[listData[0]] }}</span
            ><br /><span class="IP">{{ node[listData[1]] }}</span>
            <span :class="'dot bg-' + node.status"></span>
            <a
              id="remove-button"
              :class="
                tab == 'Group' && node.name == 'all'
                  ? 'btn btn-danger btn-sm disabled'
                  : 'btn btn-danger btn-sm'
              "
              @click.stop="remove_node(index)"
            >
              <span
                class="material-icons"
                style="font-size: 18px; vertical-align: -3px"
                >remove</span
              >
            </a>
          </div>
        </div>
      </div>
    </div>

    <vue-editor
      ref="new"
      @submit="submitNewHost"
      v-if="showForm"
      :title="'New ' + tab"
      id="0"
      :filename="filename"
      :extraData="extraData"
    ></vue-editor>
    <vue-editor
      ref="edit"
      @submit="submitEditHost"
      v-if="showEdit"
      :title="'Edit ' + tab"
      id="0"
      :filename="filename"
      :init="activeNode"
      :key="active_nodes[0]"
      :extraData="extraData"
    ></vue-editor>

    <!-- the key thing up there makes it recreate and it fixed everything i hate js -->
  </div>
</template>

<script lang="ts">
import vueEditor from "./vueEditor.vue";

import Vue from "vue";
import axios from "axios";
import VueAxios from "vue-axios";
import { log } from "console";

Vue.use(VueAxios, axios);

export default Vue.extend({
  name: "nodeVue",
  props: ["value", "listData", "filename", "extraData", "tab", "initactive"],
  data: function () {
    return {
      active_nodes: this.initactive != undefined ? [this.initactive] : [],
      nodeSearch: "",
      ip_add: "",
      showForm: false,
      showEdit: false,
      lastCall: Date.now(),
    };
  },
  computed: {
    filtered_node_list() {
      // dynamic search bar
      return this.node_list.filter((node) => {
        return node.name.toLowerCase().includes(this.nodeSearch.toLowerCase());
      });
    },
    activeNode() {
      return this.node_list[this.active_nodes[0]];
    },
    node_list() {
      return this.value;
      // this is the secret to making data reactive on prop change it has to be computed
    },
  },
  methods: {
    submitEditHost(node) {
      if (Date.now() - this.lastCall < 100) {
        // for some reason when a nodePicker was used
        // this was firing twice and would replace both
        // the selected node and the first one in the list
        // please forgive me for my sins
        return;
      } else {
        this.lastCall = Date.now();
      }
      var url = "/submit/";
      var data = node;
      data.id = this.active_nodes[0];
      console.log(node);
      Vue.axios
        .post(
          url,
          { tab: this.filename, action: "edit", data: data },
          { withCredentials: true, timeout: 5000 }
        )
        .then((response) => {
          // this.node_list[this.active_nodes[0]] = response.data
          this.node_list.splice(this.active_nodes[0], 1, response.data);
          // ^ i hate vue

          // this outer for loop is probably unnecessary just edit it when it comes in

          for (var i = 0; i < this.node_list.length; i++) {
            if (this.node_list[i].meta) {
              for (var j = 0; j < this.node_list[i].meta.length; j++) {
                if (!this.node_list[i].meta[j].key) {
                  this.node_list[i].meta[j] = {
                    key: Object.keys(this.node_list[i].meta[j])[0],
                    value: Object.values(this.node_list[i].meta[j])[0],
                  };
                }
              }
            }
          }
          this.showEdit = false;
          this.active_nodes = [];
          this.$emit("input", this.node_list);
        });
    },
    submitNewHost(node) {
      var url = "/submit/";
      console.log({ tab: this.filename, action: "add", data: node });
      Vue.axios
        .post(
          url,
          { tab: this.filename, action: "add", data: node },
          { withCredentials: true, timeout: 5000 }
        )
        .then((response) => {
          // this.node_list[this.active_nodes[0]] = response.data
          this.node_list.push(response.data);
          // ^ i hate vue

          console.log(JSON.parse(JSON.stringify(this.node_list)));
          for (var i = 0; i < this.node_list.length; i++) {
            if (this.node_list[i].meta) {
              for (var j = 0; j < this.node_list[i].meta.length; j++) {
                if (!this.node_list[i].meta[j].key) {
                  this.node_list[i].meta[j] = {
                    key: Object.keys(this.node_list[i].meta[j])[0],
                    value: Object.values(this.node_list[i].meta[j])[0],
                  };
                }
              }
            }
          }
          console.log(JSON.parse(JSON.stringify(this.node_list)));
          this.showForm = false;
          this.active_nodes = [];
          this.$emit("input", this.node_list);
        })
        .catch((error) => {
          this.$refs.new.$bvToast.show("error-message");
        });
    },
    addNode: function () {
      this.showForm = true;
      this.showEdit = false;
      this.active_nodes = [null];
      this.$emit("nodePicked", false);
    },
    remove_node: function (id) {
      var url = "/submit/";
      Vue.axios
        .post(url, {
          tab: this.filename,
          action: "delete",
          data: this.node_list[id],
        })
        .then((response) => {
          this.node_list.splice(id, 1);

          for (var i = 0; i < this.node_list.length; i++) {
            if (i >= id) {
              this.node_list[i].id--;
            }
          }

          this.active_nodes = this.active_nodes.filter(function (e) {
            return e != id;
          });
          this.showForm = false;
          this.showEdit = false;
          this.$emit("nodePicked", false);
        });
      // TODO: confirm button
    },

    refresh_nodes: function () {
      this.$emit("refresh");
    },

    nodeButtonHandler: function (node_id) {
      this.active_nodes = [node_id];
      this.showForm = false;
      this.showEdit = true;
      this.$emit("nodePicked", this.activeNode);
    },
    pluralize(word: String): String {
      return this.$pluralize(word);
    },
  },
  mounted() {},
  components: {
    "vue-editor": vueEditor,
  },
});
</script>