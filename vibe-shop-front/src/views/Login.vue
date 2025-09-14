<template>
  <div class="container" style="max-width:520px">
    <div class="card">
      <h2>Вход</h2>
      <input v-model="username" placeholder="Имя пользователя" />
      <input v-model="password" placeholder="Пароль" type="password" />
      <button class="btn btn-primary" @click="login">Войти</button>
    </div>
  </div>
  
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "../store/auth";
import { useRouter } from "vue-router";

const username = ref("");
const password = ref("");
const auth = useAuthStore();
const router = useRouter();

const login = async () => {
  try {
    await auth.login(username.value, password.value);
    router.push("/profile");
  } catch (e) {
    alert("Ошибка входа");
  }
};
</script>
