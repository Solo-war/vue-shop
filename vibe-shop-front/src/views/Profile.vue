<template>
  <div class="container" style="max-width:720px">
    <div v-if="auth.user" class="card">
      <h2>Welcome, {{ auth.user.username }} ({{ auth.user.role }})</h2>
      <div class="spacer"></div>
      <button class="btn btn-secondary" @click="auth.logout">Logout</button>
    </div>
    <div v-else class="card">
      <p class="muted">Please log in</p>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from "../store/auth";
const auth = useAuthStore();
auth.fetchUser();
</script>
