// ESLint flat config — minimal no-undef check to prevent missing imports
import js from '@eslint/js';
import globals from 'globals';

export default [
  {
    files: ['src/**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      'no-undef': 'error',
      'no-unused-vars': 'off',
      'no-empty': 'off',
      'no-unused-expressions': 'off',
      'no-useless-catch': 'off',
      'no-useless-escape': 'off',
      'no-prototype-builtins': 'off',
      'no-constant-condition': 'off',
      'no-self-assign': 'off',
      'no-sparse-arrays': 'off',
      'no-misleading-character-class': 'off',
      'no-control-regex': 'off',
      'no-fallthrough': 'off',
      'no-dupe-keys': 'off',
      'no-cond-assign': 'off',
      'no-func-assign': 'off',
      'no-irregular-whitespace': 'off',
      'no-redeclare': 'off',
      'no-case-declarations': 'off',
      'no-undef-init': 'off',
    },
  },
  {
    ignores: ['build/**', 'node_modules/**', 'public/**'],
  },
];
