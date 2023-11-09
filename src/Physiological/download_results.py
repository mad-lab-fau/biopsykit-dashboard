import io
import zipfile
import biopsykit as bp

import pandas as pd
import panel as pn
import seaborn as sns
from biopsykit.protocols import CFT
import fau_colors
from matplotlib import pyplot as plt

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import DOWNLOAD_RESULT_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.utils import get_datetime_columns_of_data_frame


def delete_timezone_of_datetime_columns_(df):
    datetime_columns = get_datetime_columns_of_data_frame(df)
    for col in datetime_columns:
        df[col] = df[col].dt.tz_localize(None)
    return df


# noinspection PyUnusedLocal
class DownloadResults(PhysiologicalBase):
    load_plots_ecg = pn.widgets.Checkbox(name="Download ECG Plots")
    load_plots_eeg = pn.widgets.Checkbox(name="Download EEG Plots")
    load_plots_hrv = pn.widgets.Checkbox(name="HRV")
    load_plots_cft = pn.widgets.Checkbox(name="Download CFT Plots")
    load_plt_hr_ensemble = pn.widgets.Checkbox(name="HR Ensemble")
    zip_buffer = io.BytesIO()

    def __init__(self, **params):
        self.download_btn = None
        params["HEADER_TEXT"] = DOWNLOAD_RESULT_TEXT
        super().__init__(**params)
        self.update_step(10)
        self._load_results_checkbox = pn.widgets.Checkbox(name="Load Results")
        self._view = pn.Column(self.header)
        self._view.append(self._load_results_checkbox)
        self._view.append(self.load_plots_hrv)
        # self._view.append(self.load_plots_ecg)

    def get_selected_files(self):
        print("get selected files")
        pn.state.notifications.info("Loading Results")
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            if self.signal == "ECG":
                self.load_ecg_files(zip_file)
            elif self.signal == "EEG":
                self.load_eeg_files(zip_file)
            elif self.signal == "CFT":
                self.load_cft_files(zip_file)
        self.zip_buffer.seek(0)
        pn.state.notifications.info("Results loaded")
        return self.zip_buffer

    def load_eeg_files(self, zip_file):
        for key in self.eeg_processor.keys():
            df = self.eeg_processor[key].eeg_result["Data"]
            df = df.tz_localize(None)
            df.to_excel(f"eeg_result_{key}.xlsx", sheet_name=key)
            zip_file.write(f"eeg_result_{key}.xlsx")
        if self.load_plots_eeg.value:
            self.load_eeg_plots(zip_file)

    def load_cft_files(self, zip_file):
        for key in self.cft_processor.keys():
            df_cft = self.cft_processor[key]["CFT"]
            df_cft = df_cft.tz_localize(None)
            df_cft.to_excel(f"cft_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_{key}.xlsx")
            df_hr = self.cft_processor[key]["HR"]
            df_hr = df_hr.tz_localize(None)
            df_hr.to_excel(f"cft_hr_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_hr_{key}.xlsx")
            df_baseline = {
                "Baseline": [
                    self.cft_processor[key]["Baseline"],
                ]
            }
            df_baseline = pd.DataFrame.from_dict(df_baseline)
            df_baseline.to_excel(f"cft_baseline_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_baseline_{key}.xlsx")
            df_cft_parameters = self.cft_processor[key]["CFT Parameters"]
            df_cft_parameters = delete_timezone_of_datetime_columns_(df_cft_parameters)
            df_cft_parameters.to_excel(f"cft_parameters_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_parameters_{key}.xlsx")
        if self.load_plots_cft.value:
            self.load_cft_plots(zip_file)

    def load_ecg_files(self, zip_file):
        if self.load_plots_ecg.value:
            self.load_ecg_plots(zip_file)
        if self.load_plots_hrv.value:
            self.load_hrv_plots(zip_file)
        if type(self.ecg_processor) != dict:
            if isinstance(self.ecg_processor.ecg_result, dict):
                for key in self.ecg_processor.ecg_result.keys():
                    df = self.ecg_processor.ecg_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"ecg_result.xlsx", sheet_name=key)
                    zip_file.write(f"ecg_result.xlsx")
            if isinstance(self.ecg_processor.hr_result, dict):
                for key in self.ecg_processor.hr_result.keys():
                    df = self.ecg_processor.hr_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"hr_result.xlsx")
                    zip_file.write(f"hr_result.xlsx")
            return
        for subject in self.ecg_processor.keys():
            if isinstance(self.ecg_processor[subject].ecg_result, dict):
                for key in self.ecg_processor[subject].ecg_result.keys():
                    df = self.ecg_processor[subject].ecg_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"ecg_result_{key}.xlsx", sheet_name=key)
                    zip_file.write(f"ecg_result_{key}.xlsx")
            if isinstance(self.ecg_processor[subject].hr_result, dict):
                for key in self.ecg_processor[subject].hr_result.keys():
                    df = self.ecg_processor[subject].hr_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"hr_result_{key}.xlsx")
                    zip_file.write(f"hr_result_{key}.xlsx")

    def load_hrv_plots(self, zip_file):
        for subject in self.ecg_processor.keys():
            for key in self.ecg_processor[subject].ecg_result.keys():
                buf = io.BytesIO()
                fig, axs = bp.signals.ecg.plotting.hrv_plot(
                    self.ecg_processor[subject], key=key
                )
                fig.savefig(buf)
                zip_file.writestr(f"HRV_{key}.png", buf.getvalue())

    def load_ecg_plots(self, zip_file):
        print("load ecg plots")
        if isinstance(self.ecg_processor, dict):
            for subject in self.ecg_processor.keys():
                print(f"Subject: {subject}")
                for key in self.ecg_processor[self.subject].ecg_result.keys():
                    print(f"Key: {key}")
                    print("create ecg plot")
                    buf = io.BytesIO()
                    fig, axs = bp.signals.ecg.plotting.ecg_plot(
                        self.ecg_processor[subject], key=key
                    )
                    fig.savefig(buf)
                    zip_file.writestr(f"ECG_{key}_{subject}.png", buf.getvalue())
        elif type(self.ecg_processor) != dict:
            buf = io.BytesIO()
            fig, axs = bp.signals.ecg.plotting.ecg_plot(self.ecg_processor, key="Data")
            fig.savefig(buf)
            zip_file.writestr(f"ECG.png", buf.getvalue())
        print("load ecg plots done")

    def load_eeg_plots(self, zip_file):
        for key in self.eeg_processor.keys():
            buf = io.BytesIO()
            palette = sns.color_palette(fau_colors.cmaps.faculties)
            sns.set_theme(
                context="notebook", style="ticks", font="sans-serif", palette=palette
            )
            fig, ax = plt.subplots(figsize=(10, 5))
            self.eeg_processor[key].eeg_result["Data"].plot(ax=ax)
            fig.savefig(buf)
            zip_file.writestr(f"ECG_{key}.png", buf.getvalue())

    def load_cft_plots(self, zip_file):
        palette = sns.color_palette(fau_colors.cmaps.faculties)
        sns.set_theme(
            context="notebook", style="ticks", font="sans-serif", palette=palette
        )
        cft = CFT()
        for key in self.cft_processor.keys():
            buf = io.BytesIO()
            fig, ax = plt.subplots(figsize=(10, 5))
            fig, _ = bp.signals.ecg.plotting.hr_plot(self.cft_processor[key]["HR"])
            fig.savefig(buf)
            zip_file.writestr(f"HR_{key}.png", buf.getvalue())
            fig, _ = cft.cft_plot(self.cft_processor[key]["HR"])
            buf = io.BytesIO()
            fig.savefig(buf)
            zip_file.writestr(f"CFT_{key}.png", buf.getvalue())

    def panel(self):
        self._load_results_checkbox.name = f"Load {self.signal} Results"
        if self.skip_hrv:
            self.load_plots_hrv.visible = False
        if self.download_btn is None:
            self.download_btn = pn.widgets.FileDownload(
                callback=self.get_selected_files, filename="Results.zip"
            )
            self._view.append(self.download_btn)
        else:
            self.download_btn.filename = "Results.zip"
        return self._view
