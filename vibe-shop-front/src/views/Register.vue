<template>
  <div class="container" style="max-width:520px">
    <div class="card">
      <h2>Register</h2>
      <input v-model="username" placeholder="Username" />
      <input v-model="password" placeholder="Password" type="password" />
      <button class="btn btn-primary" @click="register">Register</button>
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
    router.push("/login");
  } catch (e) {
    alert("Registration failed");
  }
};
</script>
