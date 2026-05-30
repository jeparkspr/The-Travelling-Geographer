import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from '@/router'
import App from '@/App.vue'

import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'

// PrimeVue Components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import FileUpload from 'primevue/fileupload'
import Tag from 'primevue/tag'
import Rating from 'primevue/rating'
import DatePicker from 'primevue/datepicker'
import Card from 'primevue/card'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Toolbar from 'primevue/toolbar'
import Menu from 'primevue/menu'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import Breadcrumb from 'primevue/breadcrumb'
import Chip from 'primevue/chip'
import Badge from 'primevue/badge'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import RadioButton from 'primevue/radiobutton'
import SelectButton from 'primevue/selectbutton'
import ToggleSwitch from 'primevue/toggleswitch'
import OverlayPanel from 'primevue/overlaypanel'
import Tooltip from 'primevue/tooltip'

// Styles
import 'primeicons/primeicons.css'
import 'leaflet/dist/leaflet.css'
import '@/assets/styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: '[data-theme="dark"]' } } })
app.use(ToastService)
app.use(ConfirmationService)

// Register PrimeVue components globally
app.component('Button', Button)
app.component('InputText', InputText)
app.component('Textarea', Textarea)
app.component('Dropdown', Select)
app.component('Select', Select)
app.component('MultiSelect', MultiSelect)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Dialog', Dialog)
app.component('FileUpload', FileUpload)
app.component('Tag', Tag)
app.component('Rating', Rating)
app.component('Calendar', DatePicker)
app.component('DatePicker', DatePicker)
app.component('Card', Card)
app.component('Tabs', Tabs)
app.component('TabList', TabList)
app.component('Tab', Tab)
app.component('TabPanels', TabPanels)
app.component('TabPanel', TabPanel)
app.component('Toolbar', Toolbar)
app.component('Menu', Menu)
app.component('Toast', Toast)
app.component('ConfirmDialog', ConfirmDialog)
app.component('Breadcrumb', Breadcrumb)
app.component('Chip', Chip)
app.component('Badge', Badge)
app.component('ProgressBar', ProgressBar)
app.component('Skeleton', Skeleton)
app.component('InputNumber', InputNumber)
app.component('Checkbox', Checkbox)
app.component('RadioButton', RadioButton)
app.component('SelectButton', SelectButton)
app.component('ToggleSwitch', ToggleSwitch)
app.component('OverlayPanel', OverlayPanel)

app.directive('tooltip', Tooltip)

app.mount('#app')
