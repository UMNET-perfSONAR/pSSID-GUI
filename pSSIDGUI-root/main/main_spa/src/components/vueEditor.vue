<template>
  <div>
    <div class="new-object-form border rounded">
      <h2 class="text-center">{{ title }}</h2>
      <form-json
        :btnReset="
          isAll
            ? {
                value: 'Reset',
                class: 'btn btn-primary disabled',
              }
            : {
                value: 'Reset',
                class: 'btn btn-primary',
              }
        "
        :btnSubmit="
          isAll
            ? {
                value: 'Submit',
                class: 'btn btn-success disabled',
              }
            : {
                value: 'Submit',
                class: 'btn btn-success',
              }
        "
        :camelizePayloadKeys="false"
        :formFields="jsonFields"
        mandatoryAsteriskLegend=""
        :resetFormAfterSubmit="false"
        formName="newnode"
      >
        <!-- hey future me its me past you here to show you how this works -->
        <!-- just incase its been a really long time the structure goes -->
        <!-- app > nodevue > vueeditor > jsonform > custominput -->
        <!-- jsonform reads the json to see which slots to put in the template for <form-json> -->
        <!-- then the v-for reads the json again to see what the slot names should be -->
        <!-- the slots replace the elements inside the form-json to render a bootstrap vue input instead of the default -->
        <!-- the bootstrap vue stuff is in custominput -->

        <!-- fill slots for vue-form-json -->
        <template
          v-for="(item, index) in jsonFields"
          v-slot:[item.slot]="{ updateFormValues, isFormReseted }"
        >
          <div :key="index">
            <hr />
            <b-row>
              <b-col>
                <component
                  :is="item.componentname"
                  :ref="item.slot"
                  v-bind="item.props"
                  :isFormReseted="isFormReseted"
                  :extraData="item.extraData"
                  @updateFormValues="updateFormValues"
                >
                </component>
              </b-col>
            </b-row>
          </div>
        </template>
      </form-json>

      <b-button
        v-if="showMetadata"
        type="button"
        style="width: 100%"
        @click="newMetadata"
        
        >
        <span v-if="filename=='test' || filename=='archiver'">
          Add Additional Option
        </span>
        <span v-else>
          New Metadata
        </span>
        </b-button
      >
      <!-- :disabled="isAll" -->
    </div>
  </div>
</template>

<script lang="ts">
import Vue from "vue"
import "vue-form-json/dist/vue-form-json.css";
import formJson from "vue-form-json";

import customInput from "./inputTypes/customInput.vue";
import metadataInput from "./inputTypes/metadataInput.vue";
import cronInput from "./inputTypes/cronInput.vue";
import channelPicker from "./inputTypes/channelPicker.vue";
import nodePicker from "./inputTypes/nodePicker.vue";
import checkboxInput from "./inputTypes/checkboxInput.vue";
import authMethod from "./inputTypes/authMethod.vue";
import jsonEditor from "./inputTypes/jsonEditor.vue";
import { log } from "console";

// import * as inputTypes from './inputTypes'

export default Vue.extend({
  components: {
    formJson,
    "custom-input": customInput,
    "metadata-input": metadataInput,
    "cron-input": cronInput,
    "channel-picker": channelPicker,
    "node-picker": nodePicker,
    "checkbox-input": checkboxInput,
    "auth-method": authMethod,
    "json-editor": jsonEditor,
  },
  props: {
    title: {
      type: String,
    },
    filename: {
      type: String,
    },
    init: {
      type: Object,
      default: function () {
        return {};
      },
    },
  },

  data: function () {
    return {
      jsonFields: [],
      meta_start: null,
    };
  },
  computed: {
    isAll() {
      // return this.filename == "group" && this.init.name == "all";
      return false
    },
    showMetadata() {
      // return "meta" in this.init;
      return this.filename == "host" || this.filename == "group" || this.filename == "test" || this.filename == "archiver"
    },
  },
  methods: {
    newMetadata: function () {
      this.$refs.meta[0].newMeta();
    },

    initfunction() {
      // set slots for vue-form-json
      this.jsonFields = require("../assets/" + this.filename + ".json");

      for (var item of this.jsonFields) {
        item.props.initvalue = null;
        item.props.disabled = null;
        if (this.isAll && item.slot != "batches") {
          item.props.disabled = true;
        }
      }
      // these 3 lines are probably like top 10 stupidest bugs i have ever fixed
      // without them initvalue isnt reactive in the components
      // doesnt initvalue get changed in the next code segment anyway? yes it does
      // i dont think ill ever figure out why i need these 3 lines
      // im going to bed

      if (
        this.showMetadata &&
        this.jsonFields[this.jsonFields.length - 1].slot != "meta"
      ) {
        this.jsonFields.push({
          slot: "meta",
          componentname: "metadata-input",
          props: {},
        });
      }
      // console.log(this.jsonFields);
      // console.log(this.init);

      // check if the node from server has a matching slot in jsonfields

      this.jsonFields.forEach((item, index) => {
        if (item.extraData) {
          for (var property in item.extraData) {
            if (
              this.$parent.$parent.$parent.$parent.$data[
                item.extraData[property]
              ] != undefined
            ) {
              item.extraData[property] =
                this.$parent.$parent.$parent.$parent.$data[
                  item.extraData[property]
                ];
            }
            // ok look i know it looks bad but to fix this id need to load the json in app.vue
            // where the server data is but thats stupid because app doesnt know what tab is open
            // i mean technically it does but also im not reusing vueeditor anywhere else itll be
            // fine just dont tell anyone this line is here shhh its our secret
          }
        }
        if (this.init[item.slot] != undefined) {
          item.props.initvalue = this.init[item.slot];
        } else if (Object.keys(this.init).length === 0) {
          item.props.initvalue = null;
        }
      });

      this.$root.$on("formSubmitted", (values) => {
        if (document.querySelector("#json-editor-form") != null) {
          if (document.querySelector("#json-editor-form").children.length == 0){
            this.$emit("submit", values.values);
            return
          }
          Object.assign(values.values, {
            spec: this.$root.jseditor.getValue(),
          });
          console.log(values.values);
          
          // values.values["extra"] = {}

          // for (var item of values.values.meta){
          //   Object.assign(values.values.extra, item)
          // }
          // dont use libraries that edit the dom worst mistake of my life

          // vvv add default values so that startval in JSONEditor includes empty form entries
          for (var group in this.$root.jseditor.schema["properties"]) {
            if (group != "schema") {
              for (var entry in this.$root.jseditor.schema["properties"][group][
                "properties"
              ]) {
                if (!(entry in this.$root.jseditor.getValue()[group])) {
                  values.values.spec[group][entry] =
                    this.$root.jseditor.schema["properties"][group][
                      "properties"
                    ][entry].default;
                }
              }
            }
          }
        }
        this.$emit("submit", values.values);
      });
    },
  },
  mounted() {
    this.initfunction();
  },
  watch: {
    // when init changes (when form is submitted) redo init
    init: {
      handler(newvar, oldvar) {
        this.initfunction();
      },
      deep: true,
    },
  },
});
</script>
