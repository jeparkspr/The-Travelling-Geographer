import { ref, computed, watch } from 'vue'

const ALLOWED_SYMBOLS = new Set('!@#$%^&*()-_=+[]{}|;:\',."/ ?')
const ALLOWED_SYMBOLS_DISPLAY = '! @ # $ % ^ & * ( ) - _ = + [ ] { } | ; : \' , . " / ? space'

export function usePasswordValidation(passwordRef) {
  const touched = ref(false)

  const rules = computed(() => {
    const pw = passwordRef.value || ''
    return [
      { label: 'At least 12 characters', met: pw.length >= 12 },
      { label: 'One uppercase letter (A–Z)', met: /[A-Z]/.test(pw) },
      { label: 'One lowercase letter (a–z)', met: /[a-z]/.test(pw) },
      { label: 'One number (0–9)', met: /[0-9]/.test(pw) },
      { label: 'One special character', met: [...pw].some(ch => ALLOWED_SYMBOLS.has(ch)) },
    ]
  })

  const disallowedChar = computed(() => {
    const pw = passwordRef.value || ''
    for (const ch of pw) {
      if (!/[a-zA-Z0-9]/.test(ch) && !ALLOWED_SYMBOLS.has(ch)) {
        return ch
      }
    }
    return null
  })

  const isValid = computed(() => {
    return rules.value.every(r => r.met) && disallowedChar.value === null
  })

  // Mark as touched once user starts typing
  watch(passwordRef, (val) => {
    if (val && val.length > 0) touched.value = true
  })

  return {
    rules,
    disallowedChar,
    isValid,
    touched,
    ALLOWED_SYMBOLS_DISPLAY,
  }
}
