<template>
  <el-container style="height: 100vh" >
  <el-header :height="header_height">
    <el-row align="middle" style="height: 100%">
      <el-col align="left" style="font-size: var(--el-font-size-extra-large)">References Reader</el-col>
    </el-row>
  </el-header>
  <el-container :style="calHeight">
    <el-aside :width="isCollapse?'64px':'200px'" style="height: 100%">
      <el-menu :default-active="$route.path" class="el-menu-vertical-demo" :collapse="isCollapse" style="height: 100%" router>
      <div class="toggle-button" @click="toggleCollapse">
        <el-icon><expand /></el-icon>
      </div>
    <el-menu-item index="/">
      <el-icon><upload-filled /></el-icon>
      <template #title>Upload Paper</template>
    </el-menu-item>
    <el-menu-item index="/Raw_References">
      <el-icon><list /></el-icon>
      <template #title>Raw References</template>
    </el-menu-item>
    <el-menu-item index="/BibTex">
      <el-icon><document /></el-icon>
      <template #title>BibTex</template>
    </el-menu-item>
  </el-menu>
      </el-aside>
      <el-main>
        <router-view/>
      </el-main>
  </el-container>
</el-container>
</template>

<script>

export default {
  name: 'App',
  components: {
  },
  methods:
    {
      toggleCollapse () {
        this.isCollapse = !this.isCollapse
      },
      
    },
    data()
    {
      return{ 
        isCollapse:true,
        header_height:"60px",
      }
      
    },
    computed: {
      calHeight()
      {
          return `height : calc( 100% - ${this.header_height} );`
      }
      }
}




</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

</style>
