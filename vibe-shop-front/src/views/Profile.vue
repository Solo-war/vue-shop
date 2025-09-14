<template>
  <div class="container" style="max-width:720px">
    <div v-if="auth.user" class="card">
      <h2>Добро пожаловать, {{ auth.user.username }} ({{ auth.user.role }})</h2>
      <div class="spacer"></div>
      <button class="btn btn-secondary" @click="auth.logout">Выйти</button>
    </div>
    <div v-else class="card">
      <p class="muted">Пожалуйста, войдите</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../store/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

auth.fetchUser();

onMounted(() => {
  if (route.query.welcome) {
    setTimeout(() => {
      const role = auth.user?.role;
      if (role === 'admin') {
        router.replace('/admin');
      } else {
        router.replace('/');
      }
    }, 3000);
  }
});
</script>
