<template>
  <!-- html for inputs, should be v-modeled or equivalent to value -->
  <!-- also needs to emit a handleInput on input -->
  <!-- see authMethod for examples of chaining other input types together -->
  <b-container>
    <b-row>
      <b-col cols="3">
        <label :for="title" class="textlabel">{{
          label ? label : title
        }}</label>
      </b-col>
      <b-col lg="8">
        <ValidationProvider rules="required" v-slot="{ errors }">
          <b-form-input
            :placeholder="placeholder"
            v-model="value"
            @input="handleInput"
            :type="type"
            :class="errors[0] ? 'is-danger' : ''"
            :id="title"
            :disabled="disabled"
          ></b-form-input>
        </ValidationProvider>
      </b-col>
    </b-row>
  </b-container>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";
Vue.use(BootstrapVue);

export default Vue.extend({
  // props that get filled in from the props option in the json schema
  props: [
    "title",
    "placeholder",
    "isFormReseted",
    "initvalue",
    "type",
    "label",
    "disabled",
  ],

  // value needs a "default constructor" for when initvalue is null
  // otherwise set value equal to initvalue
  data: function () {
    if (this.initvalue != null) {
      return {
        value: this.initvalue,
      };
    } else {
      return {
        value: null,
      };
    }
  },
  watch: {
    // reset the input type, clear any data and updateformvalue
    isFormReseted(val) {
      if (val) {
        this.value = "";
        this.updateFormValue("");
      }
    },

    // watch initvalue for changes and update value accordingly, this is for the refresh button
    // i tried to make this computed but it doesnt really work sorry
    initvalue: {
      handler(val) {
        this.value = val;
      },
      deep: true,
    },
  },
  methods: {
    // needed by vueformjson
    // any time value changes you need to emit updateformvalues kinda like v-model
    updateFormValue(val) {
      if (this.type == "number"){
        val = parseInt(val)
      }
      this.$emit("updateFormValues", { [this.title]: val });
    },
    // this is kinda stupid honestly idk why i kept it in the final
    handleInput() {
      this.updateFormValue(this.value);
    },
  },
  // update the form when it mounts so that the existing data for editing nodes works
  mounted() {
    this.updateFormValue(this.value);
  },
});
</script>