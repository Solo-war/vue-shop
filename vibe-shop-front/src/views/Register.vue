<template>
  <div class="container" style="max-width:520px">
    <div class="card">
      <h2>Регистрация</h2>
      <input v-model="username" placeholder="Имя пользователя" />
      <input v-model="password" placeholder="Пароль" type="password" />
      <button class="btn btn-primary" @click="register">Зарегистрироваться</button>
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

const register = async () => {
  try {
    await auth.register(username.value, password.value);
    // Automatically log in the newly registered user
    await auth.login(username.value, password.value);
    // Navigate to profile with a welcome flag, so it auto-hides after 3s
    router.push({ path: "/profile", query: { welcome: 1 } });
  } catch (e) {
    alert("Ошибка регистрации");
  }
};
</script>
