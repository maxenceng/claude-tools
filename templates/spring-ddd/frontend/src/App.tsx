import type { JSX } from 'react'
import { useTranslation } from 'react-i18next'
import { Heading, Page, Stack } from './design-system'
import { CoursePopularity } from './training/CoursePopularity'

export default function App(): JSX.Element {
  const { t } = useTranslation('common')
  return (
    <Page>
      <Stack gap="xl">
        <Heading level={1}>{t('app.title')}</Heading>
        <CoursePopularity />
      </Stack>
    </Page>
  )
}
