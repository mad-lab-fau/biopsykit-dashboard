import io
import zipfile
import biopsykit as bp
from io import StringIO

import pandas as pd
import panel as pn
import param

from src.Physiological.processing_and_preview import ProcessingAndPreview

# ECG_results (als xlsx), HRV_results + option für die Plots
class DownloadResults(ProcessingAndPreview):
    textHeader = ""
    dict_hr_subjects = {}
    load_plots_ecg = pn.widgets.Checkbox(name="Download ECG Plots")
    load_plots_hrv = pn.widgets.Checkbox(name="HRV")
    load_plt_hr_ensemble = pn.widgets.Checkbox(name="HR Ensemble")
    zip_buffer = io.BytesIO()
    skip_hrv = param.Boolean()

    def get_selected_files(self):
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            if self.load_plots_ecg.value:
                self.load_ecg_plots(zip_file)
            if self.load_plots_hrv.value:
                self.load_hrv_plots(zip_file)
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

    def load_hrv_plots(self, zip_file):
        for key in self.ecg_processor.ecg_result.keys():
            buf = io.BytesIO()
            # self.ecg_processor.hrv_process(
            #     self.ecg_processor,
            #     key,
            #     index=self.subject,
            # )
            fig, axs = bp.signals.ecg.plotting.hrv_plot(self.ecg_processor, key=key)
            fig.savefig(buf)
            zip_file.writestr(f"HRV_{key}.png", buf.getvalue())

    def load_ecg_plots(self, zip_file):
        for key in self.ecg_processor.ecg_result.keys():
            buf = io.BytesIO()
            fig, axs = bp.signals.ecg.plotting.ecg_plot(self.ecg_processor, key=key)
            fig.savefig(buf)
            zip_file.writestr(f"ECG_{key}.png", buf.getvalue())

    def process_hrv(self):
        if self.skip_hrv:
            return
        for key in self.ecg_processor.ecg_result.keys():
            for vp in self.subj_time_dict.keys():
                self.ecg_processor.hrv_process(
                    self.ecg_processor,
                    key,
                    index=vp,
                    # hrv_types=self.hrv_types.value,
                    # correct_rpeaks=self.correct_rpeaks.value,
                )
        pn.state.notifications.success("HRV processed successfully")
        # for vp in self.subj_time_dict.keys():
        #     self.dict_hr_subjects[vp] = self.ecg_processor.heart_rate

    def panel(self):
        self.process_hrv()
        if self.textHeader == "":
            f = open("../assets/Markdown/DownloadResults.md", "r")
            fileString = f.read()
            self.textHeader = fileString

        column = pn.Column(self.textHeader)
        download = pn.widgets.FileDownload(
            callback=self.get_selected_files, filename="Results.zip"
        )
        column.append(self.load_plots_ecg)
        if not self.skip_hrv:
            column.append(self.load_plots_hrv)
        column.append(download)
        return column
