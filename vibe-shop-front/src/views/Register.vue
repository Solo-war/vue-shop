<template>
  <div class="register-page">
    <div class="register-card">
      <h2 class="title">Регистрация</h2>
      <div class="form-group">
        <input
          v-model="username"
          placeholder="Имя пользователя"
          class="input"
        />
      </div>
      <div class="form-group">
        <input
          v-model="password"
          placeholder="Пароль"
          type="password"
          class="input"
        />
      </div>
      <button class="btn btn-primary" @click="register">
        Зарегистрироваться
      </button>
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
    await auth.login(username.value, password.value);
    router.push({ path: "/profile", query: { welcome: 1 } });
  } catch (e) {
    alert("Ошибка регистрации");
  }
};
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;

}

.register-card {
  background: rgba(255, 255, 255, 0.08);
  padding: 2rem;
  border-radius: 20px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 400px;
  text-align: center;
  backdrop-filter: blur(12px);
}

.title {
  margin-bottom: 1.5rem;
  color: #fff;
}

.form-group {
  margin-bottom: 1rem;
}

.input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: none;
  outline: none;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 1rem;
  transition: background 0.3s;
}

.input:focus {
  background: rgba(255, 255, 255, 0.25);
}

.btn {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  transition: 0.3s;
}

.btn-primary {
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  color: #fff;
}

.btn-primary:hover {
  opacity: 0.9;
}
</style>
