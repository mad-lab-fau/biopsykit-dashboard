import param
import panel as pn


class UnderConstruction(param.Parameterized):
    ready = param.Boolean(default=False)

    def panel(self):
        pane = pn.Column(
            pn.pane.Markdown(
                "# This pipeline is currently under construction, "
                "you can help us by contributing to the development of this pipeline. "
                "For further information you can click on the Info button at the header."
            ),
            pn.pane.SVG(
                link_url="https://tabler-icons.io/static/tabler-icons/icons/barrier-block.svg",
                sizing_mode="stretch_width",
                alt_text="Under Construction",
                embed=True,
                object="https://tabler-icons.io/static/tabler-icons/icons/barrier-block.svg",
            ),
        )
        return pane
