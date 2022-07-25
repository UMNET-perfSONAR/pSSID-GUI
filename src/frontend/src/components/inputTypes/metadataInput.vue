<template>
  <div>
    <div v-for="(item, index) in meta_list" :key="index">
      <ValidationProvider rules="required" v-slot="{ errors }">
        <b-form-input
          placeholder="Key..."
          v-model="meta_list[index].key"
          style="margin-bottom: 5%; display: inline; width: 30%"
          @input="handleInput"
          :class="errors[0] ? 'is-danger' : ''"
        ></b-form-input>
      </ValidationProvider>
      <!-- bruh -->
      <span> : </span>
      <ValidationProvider rules="required" v-slot="{ errors }">
        <b-form-input
          placeholder="Value..."
          v-model="meta_list[index].value"
          style="margin-bottom: 5%; display: inline; width: 40%"
          @input="handleInput"
          :class="errors[0] ? 'is-danger' : ''"
        ></b-form-input>
      </ValidationProvider>
      <a
        id="remove-meta"
        class="btn btn-danger btn-sm"
        v-on:click="removeMeta(index)"
      >
        <span
          class="material-icons"
          style="font-size: 18px; vertical-align: -3px"
          >remove</span
        >
      </a>
    </div>
  </div>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";
Vue.use(BootstrapVue);

export default Vue.extend({
  props: {
    initvalue: {
      type: Array,
      default: function () {
        return [];
      },
    },
  },
  data: function () {
    if (this.initvalue != null) {
      var output: {meta_list: any} = //todo
      {
        meta_list: this.initvalue,
      };
      return output
      
    } else {
      return {
        meta_list: [],
      };
    }
  },
  watch: {
    isFormReseted(val) {
      if (val) {
        this.meta_list = [];
        this.updateFormValue([]);
      }
    },
    initvalue: {
      handler(val) {
        this.meta_list = val;
      },
      deep: true,
    },
  },
  methods: {
    updateFormValue(val) {
      var output = [];
      for (var i = 0; i < val.length; i++) {
        output.push({ [val[i].key]: val[i].value });
      }
      this.$emit("updateFormValues", { meta: output });
    },
    handleInput() {
      this.updateFormValue(this.meta_list);
    },
    newMeta() {
      this.meta_list.push({ key: null, value: null });
    },
    removeMeta(meta_id) {
      // this.$emit("removeMeta", { meta_id: this.meta_id });
      this.meta_list.splice(meta_id, 1);
      this.updateFormValue(this.meta_list);
    },
  },
  mounted() {
    this.updateFormValue(this.meta_list);
  },
});
</script>