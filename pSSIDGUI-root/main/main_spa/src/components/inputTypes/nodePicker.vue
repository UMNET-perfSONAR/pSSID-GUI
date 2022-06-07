<template>
  <div>
    <b-row>
      <b-col>
        <span class="textlabel text-center"
          >{{ label ? label : title }} Selection</span
        >
      </b-col>
    </b-row>
    <div class="form-group" id="node-search-container">
      <b-form-input
        v-model="nodeSearch"
        type="search"
        class="node-search"
        placeholder="Search..."
        :disabled="disabled"
      />
    </div>
    <ValidationProvider :rules="optional ? '' : ''" ref="validation">
      <div
        class="list list-group"
        id="inner-node-list"
        role="tablist"
        style="max-height: 10em; overflow: auto"
      >
        <div
          v-bind:key="index"
          v-for="(node, index) in filtered_node_list"
          :id="'node-tab-' + index.toString()"
          class="node list-group-item list-group-item-action"
          v-bind:class="{
            active: single
              ? value == node[keyname]
              : value.includes(node[keyname]),
          }"
          data-bs-toggle="list"
          role="tab"
          :style="
            disabled
              ? 'display: block; cursor: not-allowed;'
              : 'display: block; cursor: pointer;'
          "
          @click="nodeButtonHandler(index)"
        >
          <span v-if="node[listData[0]]" class="name">
              <span v-if="ordered && value.includes(node[listData[0]])">
                ({{value.indexOf(node[listData[0]]) + 1}})
              </span>
          {{
            node[listData[0]]
          }}</span>
          <br />
          <span v-for="item in listData.slice(1)" :key="item">
            <span v-if="node[item]">
              <span>{{ node[item] }}</span>
            </span>
          </span>
          <span v-if="node.status" :class="'dot bg-' + node.status"></span>
        </div>
      </div>
    </ValidationProvider>
  </div>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";
Vue.use(BootstrapVue);

export default Vue.extend({
  props: [
    "title", // name of the key in output object
    "keyname", // name of the key in a node that initvalue/value corresponds to
    "isFormReseted", // skip
    "initvalue", // list of entries in the group
    "extraData", // .list refers to the outer tab to pick nodes from
    "listData", // names of the keys of nodes to show to user, first one bolded
    "single", // can you pick more than one node
    "searchkey", // name of key to use for search, default is first entry in listdata
    "label", // label, default is title
    "disabled", // used for the all group
    "optional", // is it optional
    "ordered" // the order of the selection matters, indices will be shown
  ],

  data: function () {
    if (this.initvalue != null) {
      return {
        value: this.initvalue,
        nodeSearch: "",
        hosts: this.extraData.list,
      };
    } else {
      return {
        value: this.single ? "" : [],
        nodeSearch: "",
        hosts: this.extraData.list,
      };
    }
  },
  computed: {
    filtered_node_list() {
      return this.hosts.filter((node) => {
        return node[this.searchkey ? this.searchkey : this.listData[0]]
          .toLowerCase()
          .includes(this.nodeSearch.toLowerCase());
      });
    },
  },
  watch: {
    isFormReseted(val) {
      if (val) {
        this.nodeSearch = "";
        if (this.single) {
          this.value = "";
        } else {
          this.value = [];
        }
        this.updateFormValue([]);
      }
    },
    initvalue: {
      handler(val) {
        this.value = val;
      },
      deep: true,
    },
  },
  methods: {
    updateFormValue(val) {
      this.$refs["validation"].validate(val);
      // ^^^ important this has to be in updateFormValue
      this.$emit("updateFormValues", { [this.title]: val });

      for (var i of this.hosts) {
        if (i.name == val) {
          this.$root.$emit("internalnodePicked", i);
          break;
        }
      }
    },
    handleInput() {
      this.updateFormValue(this.value);
    },
    nodeButtonHandler(node_id) {
      if (!this.disabled) {
        var nodedata = this.hosts[node_id][this.keyname];
        if (
          !this.single && this.value.includes(nodedata)
        ) {
          this.value.splice(this.value.indexOf(nodedata), 1);
        } else {
          if (this.single) {
            this.value = nodedata;
          } else {
            this.value.push(nodedata);
          }
        }
        this.updateFormValue(this.value);
      }
    },
  },
  mounted() {
    this.updateFormValue(this.value);
  },
});
</script>