<template>
  <!-- html for inputs, should be v-modeled or equivalent to value -->
  <!-- also needs to emit a handleInput on input -->
  <!-- see authMethod for examples of chaining other input types together -->
  <ValidationProvider rules="is:0" ref="validation">
    <div id="json-editor-form" />
  </ValidationProvider>
</template>

<script lang="ts">
import { BootstrapVue } from "bootstrap-vue";

import "bootstrap-vue/dist/bootstrap-vue.css";

import Vue from "vue";

import { JSONEditor } from "@json-editor/json-editor/dist/jsoneditor.js";

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
        jseditor: null,
      };
    } else {
      return {
        value: null,
        jseditor: null,
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
      this.$emit("updateFormValues", { [this.title]: val });
    },
    // this is kinda stupid honestly idk why i kept it in the final
    handleInput() {
      this.updateFormValue(this.value);
    },
  },
  created() {
    // for some reason this.jseditor keeps staying null
    // i tried for like 6 hours to fix it it is unfixable
    // i deeply regret picking jsoneditor instead of jsonforms.io
    // it just checks if this.$root.jseditor exists and adds it on in
    // vue editor on form submitted (line 300)
    if (!this.$root.listening) {
      this.$root.$on("internalnodePicked", (data) => {
        this.$root.listening = true;
        var jsonschema;
        try {
          jsonschema = require("../../assets/jsonforms/" + data.name + ".json");
        } catch (error) {
          if (this.$root.jseditor != null) {
            this.$root.jseditor.destroy();
            this.$root.jseditor = null;
          }
          return;
        }
        if (this.$root.jseditor) {
          this.$root.jseditor.destroy();
          this.$root.jseditor = null;
        }
        var valid = true;
        for (var group in this.initvalue) {
          if (group != "schema") {
            if (
              JSON.stringify(Object.keys(this.initvalue[group])) !=
              JSON.stringify(
                Object.keys(jsonschema.properties[group].properties)
              )
            ) {
              valid = false;
            }
          }
        }
        if (valid) {
          this.$root.jseditor = new JSONEditor(
            document.querySelector("#json-editor-form"),
            {
              schema: jsonschema,
              startval: this.initvalue,
              theme: "bootstrap4",
              disable_edit_json: true,
              disable_properties: true,
            }
          );
        } else {
          this.$root.jseditor = new JSONEditor(
            document.querySelector("#json-editor-form"),
            {
              schema: jsonschema,
              theme: "bootstrap4",
              disable_edit_json: true,
              disable_properties: true,
            }
          );
        }
        this.updateFormValue(this.$root.jseditor.getValue());
        if (this.$root.jseditor != null) {
          this.$root.jseditor.on("change", () => {
            this.updateFormValue(this.$root.jseditor.getValue());
            // this.$refs["validation"].validate(this.$root.jseditor.validate().length.toString())
          });
        }

        //updates the schema value in the output json depending on parameter selection
        //default schema will always be set to 1
        const frag = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.fragment"
        );
        const prot = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.protocol"
        );
        const schema = this.$root.jseditor.getEditor("root.schema");
        this.$root.jseditor.watch("root.Advanced-Groups", () => {
          if (prot.getValue() === "icmp" || prot.getValue() === "twmp") {
            schema.setValue(3);
          } else if (frag.getValue() === true || frag.getValue() === false) {
            schema.setValue(2);
          } else {
            schema.setValue(1);
          }
        });
        //enum for integer type results in error for null
        //custom validation for the parameter ip-version where the acceptable
        //values are 4 or 6
        JSONEditor.defaults.custom_validators.push((schema, value, path) => {
          if (value != null) {
            const errors = [];
            const num = value.ipversion;
            if (num <= 0 || (num >= 0 && num <= 3) || num == 5 || num >= 7) {
              // Errors must be an object with `path`, `property`, and `message`
              errors.push({
                path: "root.Everything-Else.ipversion",
                property: "format",
                message: "IP-version can either be 4 or 6",
              });
            }
            return errors;
          }
        });

        //Some Notes about throughput

        //comments about the destination and source node pattern (regex)
        //removed the two patterns that the destination and source nodes are tested against
        //Anyoneof for two patterns creates a side dropdown bar of the two validation strings
        //Which does not yield the right form we expect. Its not user friendly and also the
        //corresponsding ideal validation that needs to be done for the two patterns is
        // not done as expected by using Anyoneof.Tried using the same two patterns in the backend to get the right
        // functionlity andform but the the second pattern which is also referred as IPv6RFC2732 in pscheduler
        //dictionary throws out errors and its basically three expressions joined together.
        //Now the validation for destination and source node parameters is set up to be just the type
        //string. Please consult Mark Feit for the regex and information about further validation that need to be
        //done in this regard

        //Updates the value of schema based on the corresponding parameter set
        //The schema is set to 4 if congestion value is anything but the values
        // "bbr", "bic", "cubic", "htcp","reno", "vegas", "westwood", "yeah"
        // The other priority for setting up schema pretty much remains the same
        // link-rtt==> 3 single-ended==>2
        const cong = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.congestion"
        );
        const siend = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.single-ended"
        );
        const lirtt = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.link-rtt"
        );
        const bstrict = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.bandwidth-strict"
        );
        const cgarray = [
          "bbr",
          "bic",
          "cubic",
          "htcp",
          "reno",
          "vegas",
          "westwood",
          "yeah",
        ];
        const bsize = this.$root.jseditor.getEditor(
          "root.Advanced-Groups.burst-size"
        );
        // const schema = this.$root.jseditor.getEditor('root.schema');
        this.$root.jseditor.watch("root.Advanced-Groups", () => {
          if (
            (cgarray.includes(cong.getValue()) === false &&
              cong.getValue() !== "") ||
            (typeof bsize.getValue() === "string" && bsize.getValue() !== "") ||
            (typeof bstrict.getValue() === "boolean" &&
              bstrict.getValue() !== "")
          ) {
            schema.setValue(4);
          } else if (
            typeof lirtt.getValue() === "string" &&
            lirtt.getValue() !== ""
          ) {
            schema.setValue(3);
          } else if (
            typeof siend.getValue() === "boolean" &&
            siend.getValue() !== ""
          ) {
            schema.setValue(2);
          } else {
            schema.setValue(1);
          }
        });
        JSONEditor.defaults.custom_validators.push((schema, value, path) => {
          const errors = [];
          const num = value.ipversion;
          if (num <= 0 || (num >= 0 && num <= 3) || num == 5 || num >= 7) {
            // Errors must be an object with `path`, `property`, and `message`
            errors.push({
              path: "root.Everything-Else.ipversion",
              property: "format",
              message: "IP-version can either be 4 or 6",
            });
          }
          return errors;
        });
      });
    }
  },
  mounted() {
    if (this.$root.jseditor != null) {
      this.$root.jseditor.on("change", () => {
        this.$refs["validation"].validate(
          this.$root.jseditor.validate().length.toString()
        );
      });
    }
  },
});
</script>