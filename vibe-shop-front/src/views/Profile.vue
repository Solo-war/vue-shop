<template>
  <div v-if="auth.user">
    <h2>Welcome, {{ auth.user.username }} ({{ auth.user.role }})</h2>
    <button @click="auth.logout">Logout</button>
  </div>
  <div v-else>
    <p>Please log in</p>
  </div>
</template>

<script setup>
import { useAuthStore } from "../store/auth";
const auth = useAuthStore();
auth.fetchUser();
</script>
