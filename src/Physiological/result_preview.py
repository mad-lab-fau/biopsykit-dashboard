import panel as pn

from src.Physiological.process_hrv import AskToProcessHRV


class ResultsPreview(AskToProcessHRV):
    textHeader = ""
    dict_hr_subjects = {}

    def process_hrv(self):
        if self.skip_hrv:
            return
        keys = self.get_phases()
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
        if self.textHeader == "":
            f = open("../assets/Markdown/ProcessingAndPreview.md", "r")
            fileString = f.read()
            self.textHeader = fileString
        self.process_hrv()
        column = pn.Column(self.textHeader)
        return column
