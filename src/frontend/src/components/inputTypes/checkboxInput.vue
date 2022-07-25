<template>
  <b-row>
    <b-col>
      <ValidationProvider rules="" v-slot="{ errors }">
        <b-form-checkbox
          v-model="value"
          @change="handleInput"
          :class="errors[0] ? 'is-danger' : ''"
          >{{ label }}</b-form-checkbox
        >
      </ValidationProvider>
    </b-col>
  </b-row>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";
Vue.use(BootstrapVue);

export default Vue.extend({
  props: ["title", "placeholder", "isFormReseted", "initvalue", "label"],

  data: function () {
    if (this.initvalue != null) {
      return {
        value: this.initvalue,
      };
    } else {
      return {
        value: false,
      };
    }
  },
  watch: {
    isFormReseted(val) {
      if (val) {
        this.value = false;
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
      this.$emit("updateFormValues", { [this.title]: val });
    },
    handleInput() {
      this.updateFormValue(this.value);
    },
  },
  mounted() {
    this.updateFormValue(this.value);
  },
});
</script>