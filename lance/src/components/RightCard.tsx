import Image from "next/image";

const RightCard = () => {
  return (
    <div
      className="relative overflow-hidden w-1/2 h-[90%] m-10 rounded-tl-[28px] rounded-bl-[28px] p-10 text-white flex flex-col justify-end"
      style={{
        backgroundImage: `
                radial-gradient(187.61% 100.26% at 49.98% 80.27%, rgba(32, 40, 140, 0.00) 10%, #31008C 46.08%, #2B0A68 68.38%),
                url(/images/Template-2.svg)
              `,
        backgroundRepeat: "no-repeat",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="relative z-10 ml-18 mb-15 font-montserrat">
        <h2 className="text-5xl  font-medium mb-4">Lance</h2>
        <p className="text-xl font-medium mb-2">
          Reimagine Workflows. Unlock Intelligence.
        </p>
        <p className="text-xs font-normal">
          Secure. Scalable. Built for enterprise.
        </p>
      </div>
      <Image
        className="absolute w-[368px] h-[486px] -top-20 right-0 z-0"
        src="/images/topRing.svg"
        alt="Top ring decoration"
        width={368}
        height={486}
      />
      <Image
        className="absolute w-[250px] h-[250px] -bottom-5 left-0 z-0"
        src="/images/bottomRing.svg"
        alt="Bottom ring decoration"
        width={250}
        height={250}
      />
      <Image
        className="absolute top-0 left-0 z-0"
        src="/images/groupRings.svg"
        alt="Group rings decoration"
        width={200}
        height={200}
      />
    </div>
  );
};

export default RightCard;
