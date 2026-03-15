<template>
  <div class="comprehensive-score-config">
    <div class="header">
      <h2>综测成绩配置管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <i class="el-icon-plus"></i> 新建配置
      </el-button>
    </div>

    <!-- 配置列表 -->
    <el-card class="config-list">
      <el-table :data="configs" v-loading="loading">
        <el-table-column prop="name" label="配置名称" min-width="150">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            <el-tag v-if="!row.is_active" type="info" size="small">已停用</el-tag>
            {{ row.name }}
          </template>
        </el-table-column>

        <el-table-column label="权重配置" min-width="200">
          <template #default="{ row }">
            <div class="weight-display">
              <span>A类: {{ row.a_weight }}%</span>
              <span>B类: {{ row.b_weight }}%</span>
              <span>C类: {{ row.c_weight }}%</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="学业成绩字段" min-width="200">
          <template #default="{ row }">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <div>
                {{ getFieldLabel(row.academic_score_field) }}
                <el-tag v-if="row.academic_score_scale !== 1.0" size="small" type="info">
                  ×{{ row.academic_score_scale }}
                </el-tag>
              </div>
              <div style="font-size: 12px; color: #909399;">
                {{ row.academic_score_field }}
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="适用范围" min-width="150">
          <template #default="{ row }">
            <div v-if="row.applicable_grade || row.applicable_semester">
              <div v-if="row.applicable_grade">年级: {{ row.applicable_grade }}</div>
              <div v-if="row.applicable_semester">学期: {{ row.applicable_semester }}</div>
            </div>
            <span v-else>全部</span>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewConfig(row)">查看</el-button>
            <el-button size="small" type="primary" @click="editConfig(row)">编辑</el-button>
            <el-button
              v-if="!row.is_default"
              size="small"
              type="danger"
              @click="deleteConfig(row)"
            >
              删除
            </el-button>
            <el-button
              size="small"
              type="success"
              @click="showCalculateDialog(row)"
            >
              应用计算
            </el-button>
            <el-button type="info" size="small" @click="showPreviewDialog(row)">
              预览成绩
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑配置对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      width="600px"
      @close="resetForm"
    >
      <template #header>
        <div class="dialog-header">
          <span>{{ dialogMode === 'create' ? '新建配置' : '编辑配置' }}</span>
          <el-button
            v-if="dialogMode === 'create'"
            type="text"
            size="small"
            @click="loadDefaultConfig"
          >
            加载默认配置
          </el-button>
        </div>
      </template>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="140px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入配置名称"></el-input>
        </el-form-item>

        <el-form-item label="配置描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入配置描述（可选）"
          ></el-input>
        </el-form-item>

        <el-divider>权重配置</el-divider>

        <el-form-item label="A类材料权重" prop="a_weight">
          <el-slider
            v-model="formData.a_weight"
            :min="0"
            :max="100"
            show-input
            @change="adjustWeights('a')"
          ></el-slider>
        </el-form-item>

        <el-form-item label="B类材料权重" prop="b_weight">
          <el-slider
            v-model="formData.b_weight"
            :min="0"
            :max="100"
            show-input
            @change="adjustWeights('b')"
          ></el-slider>
        </el-form-item>

        <el-form-item label="C类材料权重" prop="c_weight">
          <el-slider
            v-model="formData.c_weight"
            :min="0"
            :max="100"
            show-input
            @change="adjustWeights('c')"
          ></el-slider>
        </el-form-item>

        <el-alert
          :title="`权重总和: ${totalWeight}% ${totalWeight === 100 ? '✓' : '（必须为100%）'}`"
          :type="totalWeight === 100 ? 'success' : 'warning'"
          :closable="false"
          style="margin-bottom: 20px"
        ></el-alert>

        <el-divider>学业成绩配置</el-divider>

        <el-form-item label="学业成绩字段" prop="academic_score_field">
          <el-select
            v-model="formData.academic_score_field"
            placeholder="请选择"
            @change="onFieldChange"
          >
            <el-option
              v-for="field in availableFields"
              :key="field.value"
              :label="field.label"
              :value="field.value"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>
                  {{ field.label }}
                  <el-tag v-if="field.recommended" type="success" size="small" style="margin-left: 5px">
                    推荐
                  </el-tag>
                </span>
                <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
                  {{ field.range }} {{ field.unit || '' }}
                </span>
              </div>
            </el-option>
          </el-select>
          <div class="field-description">
            {{ getFieldDescription(formData.academic_score_field) }}
          </div>
        </el-form-item>

        <el-form-item label="缩放系数" prop="academic_score_scale">
          <el-input-number
            v-model="formData.academic_score_scale"
            :min="0.1"
            :max="100"
            :step="0.1"
            :precision="1"
          ></el-input-number>
          <div class="field-description">
            用于将成绩转换为百分制。例如GPA（0-4）转百分制需要×25
          </div>
        </el-form-item>

        <el-divider>其他选项</el-divider>

        <el-form-item label="适用年级">
          <el-input v-model="formData.applicable_grade" placeholder="如：2021（可选）"></el-input>
        </el-form-item>

        <el-form-item label="适用学期">
          <el-input v-model="formData.applicable_semester" placeholder="如：2024-1（可选）"></el-input>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="formData.is_active"
            active-text="启用"
            inactive-text="停用"
          ></el-switch>
        </el-form-item>

        <el-form-item label="设为默认配置">
          <el-switch
            v-model="formData.is_default"
            active-text="是"
            inactive-text="否"
          ></el-switch>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '更新' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量计算对话框 -->
    <el-dialog
      title="批量计算综测成绩"
      v-model="showCalculateDialogVisible"
      width="500px"
    >
      <el-form :model="calculateForm" label-width="100px">
        <el-form-item label="学年">
          <el-input v-model="calculateForm.academic_year" placeholder="如：2024-2025"></el-input>
        </el-form-item>

        <el-form-item label="学期">
          <el-input v-model="calculateForm.semester" placeholder="如：2024-1"></el-input>
        </el-form-item>

        <el-form-item label="班级">
          <el-input
            v-model="calculateForm.class_name"
            placeholder="可选，不填则计算所有班级"
          ></el-input>
        </el-form-item>

        <el-alert
          title="将使用此配置计算所有符合条件的学生的综测成绩"
          type="info"
          :closable="false"
        ></el-alert>
      </el-form>

      <template #footer>
        <el-button @click="showCalculateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="executeCalculate" :loading="calculating">
          开始计算
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览成绩对话框 -->
    <el-dialog
      title="预览综测成绩"
      v-model="showPreviewDialogVisible"
      width="600px"
    >
      <el-form :model="previewForm" label-width="100px">
        <el-form-item label="学生学号">
          <el-input v-model="previewForm.student_id" placeholder="请输入学生学号"></el-input>
        </el-form-item>

        <el-form-item label="学年">
          <el-input v-model="previewForm.academic_year" placeholder="如：2024-2025"></el-input>
        </el-form-item>

        <el-form-item label="学期">
          <el-input v-model="previewForm.semester" placeholder="如：2024-1"></el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="executePreview" :loading="previewing">
            预览成绩
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 预览结果 -->
      <div v-if="previewResult" class="preview-result">
        <el-divider>预览结果</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学生姓名">{{ previewResult.student_name || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="学号">{{ previewResult.student_id }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ previewResult.class_name || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="学年学期">{{ previewResult.academic_year }}-{{ previewResult.semester }}</el-descriptions-item>
          <el-descriptions-item label="学业成绩">{{ previewResult.academic_score }}</el-descriptions-item>
          <el-descriptions-item label="A类得分">{{ previewResult.a_score }}</el-descriptions-item>
          <el-descriptions-item label="B类得分">{{ previewResult.b_score }}</el-descriptions-item>
          <el-descriptions-item label="C类得分">{{ previewResult.c_score }}</el-descriptions-item>
          <el-descriptions-item label="综测总分">
            <span style="font-weight: bold; color: #409EFF;">{{ previewResult.total_score }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="班级排名">{{ previewResult.class_rank || '暂无' }}</el-descriptions-item>
        </el-descriptions>

        <div class="score-breakdown">
          <h4>成绩构成分析</h4>
          <div class="score-chart">
            <div class="score-item" :style="{width: `${currentConfig.a_weight}%`, backgroundColor: '#409EFF'}">
              A类: {{ previewResult.a_score }} ({{ currentConfig.a_weight }}%)
            </div>
            <div class="score-item" :style="{width: `${currentConfig.b_weight}%`, backgroundColor: '#67C23A'}">
              B类: {{ previewResult.b_score }} ({{ currentConfig.b_weight }}%)
            </div>
            <div class="score-item" :style="{width: `${currentConfig.c_weight}%`, backgroundColor: '#E6A23C'}">
              C类: {{ previewResult.c_score }} ({{ currentConfig.c_weight }}%)
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showPreviewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI, commonAPI } from '@/services/api'

export default {
  name: 'ComprehensiveScoreConfig',
  setup() {
    const loading = ref(false)
    const configs = ref([])
    const showCreateDialog = ref(false)
    const showCalculateDialogVisible = ref(false)
    const showPreviewDialogVisible = ref(false)
    const dialogMode = ref('create')  // 'create' or 'edit'
    const currentConfig = ref(null)
    const submitting = ref(false)
    const calculating = ref(false)
    const previewing = ref(false)
    const formRef = ref(null)

    const availableFields = ref([])

    const formData = reactive({
      name: '',
      description: '',
      a_weight: 20,
      b_weight: 70,
      c_weight: 10,
      academic_score_field: 'weighted_average',
      academic_score_scale: 1.0,
      applicable_grade: '',
      applicable_semester: '',
      is_active: true,
      is_default: false
    })

    const calculateForm = reactive({
      config_id: null,
      academic_year: '',
      semester: '',
      class_name: ''
    })

    const previewForm = reactive({
      config_id: null,
      student_id: '',
      academic_year: '',
      semester: ''
    })

    const previewResult = ref(null)

    const formRules = {
      name: [
        { required: true, message: '请输入配置名称', trigger: 'blur' }
      ],
      academic_score_field: [
        { required: true, message: '请选择学业成绩字段', trigger: 'change' }
      ]
    }

    const totalWeight = computed(() => {
      return formData.a_weight + formData.b_weight + formData.c_weight
    })

    // 加载配置列表
    const loadConfigs = async () => {
      loading.value = true
      try {
        const response = await commonAPI.get('/v1/admin/comprehensive-score-config')
        configs.value = response.configs || []
      } catch (error) {
        ElMessage.error('加载配置失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    // 加载默认配置
    const loadDefaultConfig = async () => {
      try {
        const response = await commonAPI.get('/v1/admin/comprehensive-score/default-config')
        if (response) {
          Object.assign(formData, {
            name: response.name || '',
            description: response.description || '',
            a_weight: response.a_weight || 20,
            b_weight: response.b_weight || 70,
            c_weight: response.c_weight || 10,
            academic_score_field: response.academic_score_field || 'weighted_average',
            academic_score_scale: response.academic_score_scale || 1.0,
            applicable_grade: response.applicable_grade || '',
            applicable_semester: response.applicable_semester || '',
            is_active: response.is_active !== undefined ? response.is_active : true,
            is_default: false // 不允许创建多个默认配置
          })
          ElMessage.success('已加载默认配置')
        } else {
          ElMessage.info('没有可用的默认配置')
        }
      } catch (error) {
        ElMessage.error('加载默认配置失败: ' + error.message)
      }
    }

    // 加载可用字段
    const loadAvailableFields = async () => {
      try {
        const response = await commonAPI.get('/v1/admin/comprehensive-score-config/fields')
        availableFields.value = response.fields || []
      } catch (error) {
        console.error('加载可用字段失败:', error)
      }
    }

    // 调整权重（自动调整其他权重使总和为100%）
    const adjustWeights = (changedType) => {
      const total = totalWeight.value
      if (total === 100) return

      const others = ['a', 'b', 'c'].filter(t => t !== changedType)
      const otherTotal = others.reduce((sum, t) => sum + formData[`${t}_weight`], 0)

      if (otherTotal > 0) {
        const ratio = (100 - formData[`${changedType}_weight`]) / otherTotal
        others.forEach(t => {
          formData[`${t}_weight`] = Math.round(formData[`${t}_weight`] * ratio * 10) / 10
        })
      }
    }

    // 字段改变时更新缩放系数
    const onFieldChange = (value) => {
      const field = availableFields.value.find(f => f.value === value)
      if (field && field.scale) {
        formData.academic_score_scale = field.scale
      }
    }

    // 字段中英文映射
    const fieldLabelMap = {
      'arithmetic_average': '算术平均分',
      'weighted_average': '学分加权平均分',
      'average_gpa': '平均绩点',
      'average_credit_gpa': '平均学分绩点',
      'credit_gpa_sum': '学分绩点和'
    }

    // 获取字段标签
    const getFieldLabel = (value) => {
      // 优先使用本地映射
      if (fieldLabelMap[value]) {
        return fieldLabelMap[value]
      }
      // 如果本地没有，尝试从API获取的字段列表中查找
      const field = availableFields.value.find(f => f.value === value)
      return field ? field.label : value
    }

    // 获取字段描述
    const getFieldDescription = (value) => {
      const field = availableFields.value.find(f => f.value === value)
      return field ? field.description : ''
    }

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }

    // 重置表单
    const resetForm = () => {
      Object.assign(formData, {
        name: '',
        description: '',
        a_weight: 20,
        b_weight: 70,
        c_weight: 10,
        academic_score_field: 'weighted_average',
        academic_score_scale: 1.0,
        applicable_grade: '',
        applicable_semester: '',
        is_active: true,
        is_default: false
      })
      currentConfig.value = null
    }

    // 查看配置
    const viewConfig = (config) => {
      ElMessageBox.alert(
        `<div style="line-height: 1.8;">
          <p><strong>配置名称:</strong> ${config.name}</p>
          <p><strong>描述:</strong> ${config.description || '无'}</p>
          <p><strong>A类权重:</strong> ${config.a_weight}%</p>
          <p><strong>B类权重:</strong> ${config.b_weight}%</p>
          <p><strong>C类权重:</strong> ${config.c_weight}%</p>
          <p><strong>学业成绩字段:</strong> ${getFieldLabel(config.academic_score_field)}</p>
          <p><strong>缩放系数:</strong> ${config.academic_score_scale}</p>
          <p><strong>适用年级:</strong> ${config.applicable_grade || '全部'}</p>
          <p><strong>适用学期:</strong> ${config.applicable_semester || '全部'}</p>
          <p><strong>状态:</strong> ${config.is_active ? '启用' : '停用'}</p>
          <p><strong>是否默认:</strong> ${config.is_default ? '是' : '否'}</p>
        </div>`,
        '配置详情',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '关闭'
        }
      )
    }

    // 编辑配置
    const editConfig = (config) => {
      dialogMode.value = 'edit'
      currentConfig.value = config
      Object.assign(formData, {
        name: config.name,
        description: config.description,
        a_weight: config.a_weight,
        b_weight: config.b_weight,
        c_weight: config.c_weight,
        academic_score_field: config.academic_score_field,
        academic_score_scale: config.academic_score_scale,
        applicable_grade: config.applicable_grade,
        applicable_semester: config.applicable_semester,
        is_active: config.is_active,
        is_default: config.is_default
      })
      showCreateDialog.value = true
    }

    // 删除配置
    const deleteConfig = async (config) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除配置"${config.name}"吗？`,
          '确认删除',
          {
            type: 'warning'
          }
        )

        await commonAPI.delete(`/v1/admin/comprehensive-score/config/${config.id}`)
        ElMessage.success('删除成功')
        await loadConfigs()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败: ' + error.message)
        }
      }
    }

    // 提交表单
    const submitForm = async () => {
      try {
        await formRef.value.validate()

        if (totalWeight.value !== 100) {
          ElMessage.error('权重总和必须为100%')
          return
        }

        submitting.value = true

        if (dialogMode.value === 'create') {
          await commonAPI.post('/v1/admin/comprehensive-score/config', formData)
          ElMessage.success('创建成功')
        } else {
          await commonAPI.put(`/v1/admin/comprehensive-score/config/${currentConfig.value.id}`, formData)
          ElMessage.success('更新成功')
        }

        showCreateDialog.value = false
        await loadConfigs()
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      } finally {
        submitting.value = false
      }
    }

    // 显示计算对话框
    const showCalculateDialog = (config) => {
      calculateForm.config_id = config.id
      calculateForm.academic_year = ''
      calculateForm.semester = ''
      calculateForm.class_name = ''
      showCalculateDialogVisible.value = true
    }

    // 执行计算
    const executeCalculate = async () => {
      if (!calculateForm.academic_year || !calculateForm.semester) {
        ElMessage.warning('请填写学年和学期')
        return
      }

      try {
        calculating.value = true
        const result = await commonAPI.post('/v1/admin/comprehensive-score/calculate', {
          config_id: calculateForm.config_id,
          academic_year: calculateForm.academic_year,
          semester: calculateForm.semester,
          class_name: calculateForm.class_name || null
        })

        ElMessage.success(
          `计算完成！处理: ${result.processed}人，成功: ${result.updated}人，失败: ${result.failed}人`
        )
        showCalculateDialogVisible.value = false
      } catch (error) {
        ElMessage.error('计算失败: ' + error.message)
      } finally {
        calculating.value = false
      }
    }

    // 显示预览对话框
    const showPreviewDialog = (config) => {
      currentConfig.value = config
      previewForm.config_id = config.id
      previewForm.student_id = ''
      previewForm.academic_year = ''
      previewForm.semester = ''
      previewResult.value = null
      showPreviewDialogVisible.value = true
    }

    // 执行预览
    const executePreview = async () => {
      if (!previewForm.student_id || !previewForm.academic_year || !previewForm.semester) {
        ElMessage.warning('请填写完整信息')
        return
      }

      try {
        previewing.value = true
        const result = await commonAPI.post('/v1/admin/comprehensive-score/preview', {
          config_id: previewForm.config_id,
          student_id: previewForm.student_id,
          academic_year: previewForm.academic_year,
          semester: previewForm.semester
        })

        previewResult.value = result
      } catch (error) {
        ElMessage.error('预览失败: ' + error.message)
      } finally {
        previewing.value = false
      }
    }

    onMounted(() => {
      loadConfigs()
      loadAvailableFields()
    })

    return {
        loading,
        configs,
        showCreateDialog,
        showCalculateDialogVisible,
        showPreviewDialogVisible,
        dialogMode,
        formData,
        calculateForm,
        previewForm,
        formRules,
        formRef,
        submitting,
        calculating,
        previewing,
        availableFields,
        totalWeight,
        currentConfig,
        previewResult,
        loadConfigs,
        loadDefaultConfig,
        adjustWeights,
        onFieldChange,
        getFieldLabel,
        getFieldDescription,
        formatDate,
        resetForm,
        viewConfig,
        editConfig,
        deleteConfig,
        submitForm,
        showCalculateDialog,
        executeCalculate,
        showPreviewDialog,
        executePreview
      }
  }
}
</script>

<style scoped>
.comprehensive-score-config {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.config-list {
  margin-bottom: 20px;
}

.weight-display {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.weight-display span {
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 13px;
}

.field-description {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

:deep(.el-slider) {
  width: 100%;
}

.preview-result {
  margin-top: 20px;
}

.score-breakdown {
  margin-top: 20px;
}

.score-breakdown h4 {
  margin-bottom: 10px;
  color: #333;
}

.score-chart {
  display: flex;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.score-item {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  text-align: center;
  padding: 0 5px;
  transition: all 0.3s;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

