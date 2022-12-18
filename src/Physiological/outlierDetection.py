import param
import panel as pn
from biopsykit.signals.ecg import EcgProcessor


class OutlierDetection(param.Parameterized):
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    textHeader = ''
    textParams = ''
    methods = ['quality',
               'artifact',
               'physiological',
               'statistical_rr',
               'statistical_rr_diff']

    outlier_methods = pn.widgets.MultiChoice(name='Methods', value=['quality', 'artifact'], options=methods)
    statistical_param = pn.widgets.FloatInput(name='Statistical:', value=2.576)
    ecg_processor = None
    correlation = pn.widgets.FloatInput(name='correlation', value=0.3)
    quality = pn.widgets.FloatInput(name='quality', value=0.4)
    artifact = pn.widgets.FloatInput(name='artifact', value=0)
    statistical_rr = pn.widgets.FloatInput(name='statistical_rr', value=2.576)
    statistical_rr_diff = pn.widgets.FloatInput(name='statistical_rr_diff', value=1.96)
    physiological_upper = pn.widgets.FloatInput(name='physiological_upper', value=200)
    physiological_lower = pn.widgets.FloatInput(name='physiological_lower', value=45)

    def panel(self):
        self.ecg_processor = EcgProcessor(data=self.data, sampling_rate=self.sampling_rate)
        if self.textHeader == "":
            f = open('../assets/Markdown/OutlierDetection.html', 'r')
            fileString = f.read()
            self.textHeader = fileString
        if self.textParams == "":
            f = open('../assets/Markdown/OutlierParams.md', 'r')
            fileString = f.read()
            self.textParams = fileString
        return pn.Column(
            pn.pane.HTML(self.textHeader),
            self.outlier_methods,
            pn.pane.Markdown(self.textParams),
            self.correlation,
            self.quality,
            self.artifact,
            self.statistical_rr,
            self.statistical_rr_diff,
            pn.Row(
                self.physiological_lower,
                self.physiological_upper
            )
        )

    def get_outlier_params(self):
        return {
            'correlation': self.correlation.value,
            'quality': self.quality.value,
            'artifact': self.artifact.value,
            'statistical_rr': self.statistical_rr.value,
            'statistical_rr_diff': self.statistical_rr_diff,
            'physiological': (self.physiological_lower.value, self.physiological_upper.value)
        }

    @param.output(('ecg_processor', param.Dynamic))
    def output(self):
        self.ecg_processor.ecg_process(outlier_correction=self.outlier_methods.value,
                                       outlier_params=self.get_outlier_params())
        return self.ecg_processor
