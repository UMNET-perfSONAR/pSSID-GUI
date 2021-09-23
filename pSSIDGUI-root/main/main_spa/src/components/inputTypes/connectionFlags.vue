<template>
  <div>
    <checkbox-input
      title="paranoid"
      :initvalue="initvalue == null ? null : initvalue['paranoid']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      label="Paranoid"
      class="field"
    ></checkbox-input>
    <checkbox-input
      title="pscheduler_restart"
      :initvalue="initvalue == null ? null : initvalue['pscheduler_restart']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      label="pScheduler Restart"
      class="field"
    ></checkbox-input>
    <checkbox-input
      title="apache_restart"
      :initvalue="initvalue == null ? null : initvalue['apache_restart']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      label="Apache Restart"
      class="field"
    ></checkbox-input>
    <checkbox-input
      title="postgres_restart"
      :initvalue="initvalue == null ? null : initvalue['postgres_restart']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      label="Postgres Restart"
      class="field"
    ></checkbox-input>
    <custom-input
      title="wait_time"
      placeholder="Wait Time..."
      label="Wait Time"
      :initvalue="initvalue == null ? null : initvalue['wait_time']"
      :isFormReseted="isFormReseted"
      @updateFormValues="handleInput"
      class="field"
      type="number"
    ></custom-input>
  </div>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";
import checkboxInput from "./checkboxInput.vue";
import customInput from "./customInput.vue";

Vue.use(BootstrapVue);

export default Vue.extend({
  components: {
    "checkbox-input": checkboxInput,
    "custom-input": customInput,
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
          paranoid: null,
          pscheduler_restart: null,
          apache_restart: null,
          postgres_restart: null,
          wait_time: null,
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