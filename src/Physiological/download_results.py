import io
import zipfile
from io import StringIO

import pandas as pd
import panel as pn
from src.Physiological.processing_and_preview import ProcessingAndPreview

# ECG_results (als xlsx), HRV_results + option für die Plots
class DownloadResults(ProcessingAndPreview):
    textHeader = ""
    dict_hr_subjects = {}
    download_results = pn.widgets.FileDownload(
        name="Download Files", filename="Results.zip"
    )
    load_plots = pn.widgets.Checkbox(name="Download Plots as well")
    zip_buffer = io.BytesIO()

    def get_selected_files(self):
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            if isinstance(self.ecg_processor.ecg_result, dict):
                for key in self.ecg_processor.ecg_result.keys():
                    df = self.ecg_processor.ecg_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"ecg_result_{key}.xlsx", sheet_name=key)
                    zip_file.write(f"ecg_result_{key}.xlsx")
            if isinstance(self.ecg_processor.hr_result, dict):
                for key in self.ecg_processor.hr_result.keys():
                    df = self.ecg_processor.hr_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"hr_result_{key}.xlsx")
                    zip_file.write(f"hr_result_{key}.xlsx")
        self.zip_buffer.seek(0)
        return self.zip_buffer

    def process_hrv(self):
        if self.skip_hrv:
            return
        keys = self.ecg_processor.phases
        for key in keys:
            for vp in self.subj_time_dict.keys():
                self.ecg_processor.hrv_process(
                    self.ecg_processor,
                    key,
                    index=vp,
                    hrv_types=self.hrv_types.value,
                    correct_rpeaks=self.correct_rpeaks.value,
                )
        pn.state.notifications.success("HRV processed successfully")
        for vp in self.subj_time_dict.keys():
            self.dict_hr_subjects[vp] = self.ecg_processor.heart_rate

    def panel(self):
        self.download_results.callback = self.get_selected_files
        if self.textHeader == "":
            f = open("../assets/Markdown/DownloadResults.md", "r")
            fileString = f.read()
            self.textHeader = fileString
        # self.process_hrv()
        column = pn.Column(self.textHeader)
        column.append(self.download_results)
        return column
