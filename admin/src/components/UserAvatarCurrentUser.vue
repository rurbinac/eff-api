<script setup>
import { useAuthStore } from '@/stores/auth.js'
import UserAvatar from '@/components/UserAvatar.vue'

const auth = useAuthStore()
</script>

<template>
  <UserAvatar :username="auth.userName" :avatar="`https://api.dicebear.com/7.x/avataaars/svg?seed=${auth.userEmail}`">
    <slot />
  </UserAvatar>
</template>
