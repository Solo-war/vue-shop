<template>
  <div class="container" style="max-width:520px">
    <div class="card">
      <h2>Login</h2>
      <input v-model="username" placeholder="Username" />
      <input v-model="password" placeholder="Password" type="password" />
      <button class="btn btn-primary" @click="login">Login</button>
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
    alert("Login failed");
  }
};
</script>
