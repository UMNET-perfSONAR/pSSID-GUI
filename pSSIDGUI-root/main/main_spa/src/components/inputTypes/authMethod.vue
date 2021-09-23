<!-- subcomponents need class="field" for css reasons -->
<template>
  <div>
    <custom-input
      title="type"
      placeholder="Type..."
      label="Type"
      :initvalue="initvalue == null ? null : initvalue['type']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      class="field"
    ></custom-input>
    <custom-input
      title="UID"
      placeholder="UID..."
      label="UID"
      :initvalue="initvalue == null ? null : initvalue['UID']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      class="field"
    ></custom-input>
    <custom-input
      title="Password"
      placeholder="Password..."
      label="Password"
      :initvalue="initvalue == null ? null : initvalue['Password']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      class="field"
    ></custom-input>
    <connection-flags
      title="connection_flags"
      :initvalue="initvalue == null ? null : initvalue['connection_flags']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      class="field"
    ></connection-flags>
  </div>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";
Vue.use(BootstrapVue);

import customInput from "./customInput.vue";
import connectionFlags from "./connectionFlags.vue";

export default Vue.extend({
  components: {
    "custom-input": customInput,
    "connection-flags": connectionFlags,
  },
  props: ["title", "placeholder", "isFormReseted", "initvalue"],

  data: function () {
    if (this.initvalue != null) {
      return {
        value: this.initvalue,
      };
    } else {
      return {
        value: {
          type: null,
          UID: null,
          Password: null,
          connection_flags: null
        },
      };
    }
  },
  watch: {
    isFormReseted(val) {
      if (val) {
        this.value = {};
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
    handleInput(e) {
      Object.assign(this.value, e);
      this.updateFormValue(this.value);
    },
  },
  mounted() {
    this.updateFormValue(this.value);
  },
});
</script>