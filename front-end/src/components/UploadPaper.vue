<template>
　　<div>
      <el-upload
         class="upload-demo"
         drag
         ref="upload"
         accept=".pdf"      
         :file-list="fileList"
         :action="uploadUrl" 
         :show-file-list="true"
         :on-progress="onProgress"
         :on-success="onSuccess"
         :on-error="onError"
         :on-exceed="onExceed"
         :auto-upload="false" 
         :limit="1"
         v-loading.fullscreen.lock="fullscreenLoading"
         :element-loading-text="LoadingText"
       >
       <el-icon class="el-icon--upload"><document-add /></el-icon>
       <div class="el-upload__text">
      Drop file here or <em>click to upload</em>
      
    </div>
    <template #tip>
      <div class="el-upload__tip text-red">
        limit 1 file, new file will cover the old file
      </div>
      <el-button type="primary" @click="submit">uplaod</el-button>
    </template>
        
       </el-upload>
       
    </div>
</template>
<script>
    export default {
        name: 'Upload',
        data() {
            return{ 
				fileList: [],
                uploadUrl: '',
                fullscreenLoading: false,
                LoadingText :"正在上传..."
			}
             
        },
　　　　 methods: {
            onExceed(files) {
                this.$refs['upload'].clearFiles();
                this.$refs['upload'].handleStart(files[0])
            },
            onProgress(event) {
              if(event.total==event.loaded)this.LoadingText="上传完成，等待服务器解析..."
              // if(event.LoadingText)
                this.fullscreenLoading=true
            },
      　　　 onSuccess(res) {
                this.$store.commit('setReferencesList',res)
                this.fullscreenLoading=false
                this.$router.push("Raw_References")

            },
      　　　 onError(res) {
                this.fullscreenLoading=false
                this.$alert('Upload Fail', 'Fail', {
                    confirmButtonText: 'confirm',
                    callback: action => {
                       console.log("Upload Fail")
                    },
                })
             },
      　　    submit() {
                this.uploadUrl = 'api/upload'
                
                 this.$nextTick(() => {
                     this.$refs.upload.submit()
                 })
                 
             },
         },
    }
</script>

<style>
.el-button{
  margin : 20px;
}
</style>