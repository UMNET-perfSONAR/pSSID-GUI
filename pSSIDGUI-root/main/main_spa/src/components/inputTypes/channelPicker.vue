<template>
  <div>
    <p class="text-center">Channels (Range: '-' (inclusive) Add: ',')</p>
    <ValidationProvider rules="required" v-slot="{ errors }">
      <b-form-input
        :placeholder="placeholder"
        v-model="value"
        @input="handleInput"
        :class="errors[0] ? 'is-danger' : ''"
      ></b-form-input>
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
  props: ["title", "placeholder", "isFormReseted", "initvalue"],

  data: function () {
    if (this.initvalue == null) {
      return {
        value: null,
      };
    } else {
      return {
        value: this.initvalue.join(","),
      };
    }
  },
  watch: {
    isFormReseted(val) {
      if (val) {
        this.value = "";
        this.updateFormValue([]);
      }
    },
    initvalue: {
      handler(val) {
        this.value = val.join(",");
      },
      deep: true,
    },
  },
  methods: {
    updateFormValue(val) {
      if (val == null) {
        this.$emit("updateFormValues", { [this.title]: val });
        return;
      }
      var output = [];
      var valarr = val.replaceAll(" ", "").split(",");
      for (var item of valarr) {
        if (item.includes("-")) {
          var begin = parseInt(item.split("-")[0]);
          var end = parseInt(item.split("-")[1]);
          for (var j = begin; j <= end; j++) {
            if (!output.includes(j)) {
              output.push(j);
            }
          }
        } else {
          if (!output.includes(parseInt(item))) {
            output.push(parseInt(item));
          }
        }
      }
      this.$emit("updateFormValues", { [this.title]: output });
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