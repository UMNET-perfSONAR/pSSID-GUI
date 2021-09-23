<template>
  <div>
    <b-row>
      <b-col>
        <ValidationProvider rules="required" v-slot="{ errors }">
          <b-form-input
            placeholder="min"
            v-model="minute"
            @input="handleInput"
            :class="errors[0] ? 'is-danger' : ''"
          >
          </b-form-input>
        </ValidationProvider>
      </b-col>
      <b-col>
        <ValidationProvider rules="required" v-slot="{ errors }">
          <b-form-input
            placeholder="hour"
            v-model="hour"
            @input="handleInput"
            :class="errors[0] ? 'is-danger' : ''"
          ></b-form-input>
        </ValidationProvider>
      </b-col>
      <b-col>
        <ValidationProvider rules="required" v-slot="{ errors }">
          <b-form-input
            placeholder="day"
            v-model="day"
            @input="handleInput"
            :class="errors[0] ? 'is-danger' : ''"
          ></b-form-input>
        </ValidationProvider>
      </b-col>
      <b-col>
        <ValidationProvider rules="required" v-slot="{ errors }">
          <b-form-input
            placeholder="month"
            v-model="month"
            @input="handleInput"
            :class="errors[0] ? 'is-danger' : ''"
          ></b-form-input>
        </ValidationProvider>
      </b-col>
      <b-col>
        <ValidationProvider rules="required" v-slot="{ errors }">
          <b-form-input
            placeholder="year"
            v-model="year"
            @input="handleInput"
            :class="errors[0] ? 'is-danger' : ''"
          ></b-form-input>
        </ValidationProvider>
      </b-col>
    </b-row>
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
    if (this.initvalue != null) {
      return {
        minute: this.initvalue.minute,
        hour: this.initvalue.hour,
        day: this.initvalue.day,
        month: this.initvalue.month,
        year: this.initvalue.year,
      };
    } else {
      return {
        minute: null,
        hour: null,
        day: null,
        month: null,
        year: null,
      };
    }
  },
  watch: {
    isFormReseted(val) {
      if (val) {
        this.minute = "";
        this.hour = "";
        this.day = "";
        this.month = "";
        this.year = "";
        this.updateFormValue([]);
      }
    },
    initvalue: {
      handler(val) {
        this.minute = this.initvalue.minute;
        this.hour = this.initvalue.hour;
        this.day = this.initvalue.day;
        this.month = this.initvalue.month;
        this.year = this.initvalue.year;
      },
      deep: true,
    },
  },
  methods: {
    updateFormValue(val) {
      this.$emit("updateFormValues", {
        [this.title]: val,
        [this.title + "string"]: Object.values(this._data).join(" "),
      });
    },
    handleInput() {
      this.updateFormValue(this._data);
    },
  },
  mounted() {
    this.updateFormValue(this._data);
  },
});
</script>