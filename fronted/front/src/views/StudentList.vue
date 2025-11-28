<template>
  <div class="student-list-container">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>学生列表</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleAddStudent">
              <el-icon><Plus /></el-icon>
              添加学生
            </el-button>
            <el-button type="success" @click="handleImportStudents">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 搜索和筛选区域 -->
      <div class="filter-section">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="学号/姓名">
            <el-input
              v-model="searchForm.keyword"
              placeholder="请输入学号或姓名"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="班级">
            <el-select
              v-model="searchForm.classId"
              placeholder="请选择班级"
              clearable
              @change="handleSearch"
            >
              <el-option
                v-for="item in classOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="请选择状态"
              clearable
              @change="handleSearch"
            >
              <el-option label="正常" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 学生列表表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="studentList"
        stripe
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="80">
          <template #default="{ row }">
            <el-tag :type="row.gender === '男' ? 'primary' : 'success'">
              {{ row.gender }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="className" label="班级" width="120" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="comprehensiveScore" label="综测成绩" width="100">
          <template #default="{ row }">
            <el-tag :type="getScoreTagType(row.comprehensiveScore)">
              {{ row.comprehensiveScore || '未评分' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleViewStudent(row)"
            >
              查看
            </el-button>
            <el-button
              type="warning"
              size="small"
              link
              @click="handleEditStudent(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDeleteStudent(row)"
            >
              删除
            </el-button>
            <el-dropdown trigger="click" @command="handleCommand($event, row)">
              <el-button type="info" size="small" link>
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="resetPassword">重置密码</el-dropdown-item>
                  <el-dropdown-item command="toggleStatus">
                    {{ row.status === 'active' ? '禁用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item command="viewScores">查看成绩</el-dropdown-item>
                  <el-dropdown-item command="exportData">导出数据</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 批量操作区域 -->
    <div v-if="selectedStudents.length > 0" class="batch-actions">
      <el-card>
        <div class="batch-content">
          <span>已选择 {{ selectedStudents.length }} 项</span>
          <div class="batch-buttons">
            <el-button type="primary" @click="handleBatchExport">批量导出</el-button>
            <el-button type="warning" @click="handleBatchDisable">批量禁用</el-button>
            <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 学生详情对话框 -->
    <el-dialog
      v-model="studentDetailVisible"
      :title="isEditing ? '编辑学生' : '学生详情'"
      width="600px"
      @close="resetStudentForm"
    >
      <el-form
        ref="studentFormRef"
        :model="studentForm"
        :rules="studentRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学号" prop="studentId">
              <el-input
                v-model="studentForm.studentId"
                :disabled="!isEditing"
                placeholder="请输入学号"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input
                v-model="studentForm.name"
                :disabled="!isEditing"
                placeholder="请输入姓名"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select
                v-model="studentForm.gender"
                :disabled="!isEditing"
                placeholder="请选择性别"
              >
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级" prop="classId">
              <el-select
                v-model="studentForm.classId"
                :disabled="!isEditing"
                placeholder="请选择班级"
              >
                <el-option
                  v-for="item in classOptions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="studentForm.email"
                :disabled="!isEditing"
                placeholder="请输入邮箱"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话" prop="phone">
              <el-input
                v-model="studentForm.phone"
                :disabled="!isEditing"
                placeholder="请输入电话"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="studentForm.status" :disabled="!isEditing">
            <el-radio label="active">正常</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="studentForm.remark"
            :disabled="!isEditing"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="studentDetailVisible = false">取消</el-button>
          <el-button v-if="!isEditing" type="primary" @click="isEditing = true">
            编辑
          </el-button>
          <el-button v-else type="primary" @click="handleSubmitStudent">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="批量导入学生"
      width="500px"
    >
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls,.csv"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传xlsx/xls/csv文件，且不超过10MB
          </div>
        </template>
      </el-upload>
      <div class="import-tips">
        <p>导入说明：</p>
        <p>1. 请按照模板格式填写学生信息</p>
        <p>2. 学号不能重复</p>
        <p>3. 必填字段：学号、姓名、性别、班级</p>
        <el-button type="text" @click="downloadTemplate">下载模板</el-button>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleImportSubmit">确认导入</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search, ArrowDown, UploadFilled } from '@element-plus/icons-vue'
import { teacherAPI } from '@/services/api'

// 数据状态
const loading = ref(false)
const studentList = ref([])
const classOptions = ref([])
const selectedStudents = ref([])

// 搜索表单
const searchForm = reactive({
  keyword: '',
  classId: '',
  status: ''
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 学生详情对话框
const studentDetailVisible = ref(false)
const isEditing = ref(false)
const studentFormRef = ref(null)
const studentForm = reactive({
  id: '',
  studentId: '',
  name: '',
  gender: '',
  classId: '',
  email: '',
  phone: '',
  status: 'active',
  remark: ''
})

// 表单验证规则
const studentRules = {
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  gender: [
    { required: true, message: '请选择性别', trigger: 'change' }
  ],
  classId: [
    { required: true, message: '请选择班级', trigger: 'change' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

// 批量导入对话框
const importDialogVisible = ref(false)
const uploadRef = ref(null)
const importFile = ref(null)

// 获取学生列表
const fetchStudentList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      keyword: searchForm.keyword,
      classId: searchForm.classId,
      status: searchForm.status
    }
    
    const response = await teacherAPI.getStudentList(params)
    studentList.value = response.data || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取学生列表失败:', error)
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

// 获取班级列表
const fetchClassList = async () => {
  try {
    const response = await teacherAPI.getClassList()
    classOptions.value = response.data || []
  } catch (error) {
    console.error('获取班级列表失败:', error)
    ElMessage.error('获取班级列表失败')
  }
}

// 搜索
const handleSearch = () => {
  pagination.currentPage = 1
  fetchStudentList()
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchStudentList()
}

// 当前页变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchStudentList()
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedStudents.value = selection
}

// 获取成绩标签类型
const getScoreTagType = (score) => {
  if (!score) return 'info'
  if (score >= 90) return 'success'
  if (score >= 80) return 'warning'
  return 'danger'
}

// 添加学生
const handleAddStudent = () => {
  resetStudentForm()
  isEditing.value = true
  studentDetailVisible.value = true
}

// 查看学生详情
const handleViewStudent = (row) => {
  Object.assign(studentForm, row)
  isEditing.value = false
  studentDetailVisible.value = true
}

// 编辑学生
const handleEditStudent = (row) => {
  Object.assign(studentForm, row)
  isEditing.value = true
  studentDetailVisible.value = true
}

// 删除学生
const handleDeleteStudent = (row) => {
  ElMessageBox.confirm(
    `确定要删除学生 ${row.name} 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await teacherAPI.deleteStudent(row.id)
      ElMessage.success('删除成功')
      fetchStudentList()
    } catch (error) {
      console.error('删除学生失败:', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

// 下拉菜单命令处理
const handleCommand = (command, row) => {
  switch (command) {
    case 'resetPassword':
      handleResetPassword(row)
      break
    case 'toggleStatus':
      handleToggleStatus(row)
      break
    case 'viewScores':
      handleViewScores(row)
      break
    case 'exportData':
      handleExportData(row)
      break
  }
}

// 重置密码
const handleResetPassword = (row) => {
  ElMessageBox.confirm(
    `确定要重置学生 ${row.name} 的密码吗？`,
    '重置密码确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await teacherAPI.resetStudentPassword(row.id)
      ElMessage.success('密码重置成功，新密码为：123456')
    } catch (error) {
      console.error('重置密码失败:', error)
      ElMessage.error('重置密码失败')
    }
  }).catch(() => {
    // 用户取消重置
  })
}

// 切换状态
const handleToggleStatus = (row) => {
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  const statusText = newStatus === 'active' ? '启用' : '禁用'
  
  ElMessageBox.confirm(
    `确定要${statusText}学生 ${row.name} 吗？`,
    `${statusText}确认`,
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await teacherAPI.updateStudentStatus(row.id, newStatus)
      ElMessage.success(`${statusText}成功`)
      fetchStudentList()
    } catch (error) {
      console.error(`${statusText}失败:`, error)
      ElMessage.error(`${statusText}失败`)
    }
  }).catch(() => {
    // 用户取消操作
  })
}

// 查看成绩
const handleViewScores = (row) => {
  // 跳转到成绩详情页面
  // 这里可以根据实际需求实现
  ElMessage.info(`查看学生 ${row.name} 的成绩详情`)
}

// 导出单个学生数据
const handleExportData = (row) => {
  // 实现导出单个学生数据
  ElMessage.info(`导出学生 ${row.name} 的数据`)
}

// 批量导入
const handleImportStudents = () => {
  importDialogVisible.value = true
}

// 文件变化处理
const handleFileChange = (file) => {
  importFile.value = file.raw
}

// 提交导入
const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    
    await teacherAPI.importStudents(formData)
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    fetchStudentList()
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败')
  }
}

// 下载模板
const downloadTemplate = () => {
  // 实现下载模板功能
  ElMessage.info('下载模板')
}

// 批量导出
const handleBatchExport = () => {
  // 实现批量导出功能
  ElMessage.info('批量导出')
}

// 批量禁用
const handleBatchDisable = () => {
  // 实现批量禁用功能
  ElMessage.info('批量禁用')
}

// 批量删除
const handleBatchDelete = () => {
  // 实现批量删除功能
  ElMessage.info('批量删除')
}

// 提交学生表单
const handleSubmitStudent = async () => {
  if (!studentFormRef.value) return
  
  await studentFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (studentForm.id) {
          // 更新学生
          await teacherAPI.updateStudent(studentForm.id, studentForm)
          ElMessage.success('更新成功')
        } else {
          // 创建学生
          await teacherAPI.createStudent(studentForm)
          ElMessage.success('创建成功')
        }
        
        studentDetailVisible.value = false
        fetchStudentList()
      } catch (error) {
        console.error('保存学生信息失败:', error)
        ElMessage.error('保存失败')
      }
    }
  })
}

// 重置学生表单
const resetStudentForm = () => {
  studentForm.id = ''
  studentForm.studentId = ''
  studentForm.name = ''
  studentForm.gender = ''
  studentForm.classId = ''
  studentForm.email = ''
  studentForm.phone = ''
  studentForm.status = 'active'
  studentForm.remark = ''
  
  if (studentFormRef.value) {
    studentFormRef.value.resetFields()
  }
}

// 初始化
onMounted(() => {
  fetchStudentList()
  fetchClassList()
})
</script>

<style scoped>
.student-list-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-section {
  margin-top: 15px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.batch-actions {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.batch-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-buttons {
  display: flex;
  gap: 10px;
}

.import-tips {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.import-tips p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}
</style>