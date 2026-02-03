<template>
  <div ref="editorRef" style="width: 100%; height: 100%;"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as monaco from 'monaco-editor';

const props = defineProps({
  modelValue: String,
  language: {
    type: String,
    default: 'shell'
  },
  theme: {
    type: String,
    default: 'vs-dark'
  }
});

const emit = defineEmits(['update:modelValue']);

const editorRef = ref(null);
let editorInstance = null;

onMounted(() => {
  if (editorRef.value) {
    editorInstance = monaco.editor.create(editorRef.value, {
      value: props.modelValue,
      language: props.language,
      theme: props.theme,
      automaticLayout: true,
      minimap: { enabled: false }
    });

    editorInstance.onDidChangeModelContent(() => {
      const currentValue = editorInstance.getValue();
      emit('update:modelValue', currentValue);
    });
  }
});

watch(() => props.modelValue, (newValue) => {
  if (editorInstance && newValue !== editorInstance.getValue()) {
    editorInstance.setValue(newValue);
  }
});

onUnmounted(() => {
  if (editorInstance) {
    editorInstance.dispose();
  }
});
</script>
