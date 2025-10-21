#version 330 core

out vec4 FragColor;

// ===== Uniforms =====
uniform float uTime;
uniform vec2 uResolution;
uniform vec4 uMouse;

uniform sampler2D uChannel0; // noise
uniform sampler2D uChannel1; // building texture
uniform sampler2D uChannel2; // lights/clouds texture
uniform sampler2D uChannel3; // gallery texture

// ===== Defines =====
#define BUMPFACTOR 0.2
#define EPSILON 0.1
#define BUMPDISTANCE 200.
#define CAMERASPEED 5.
#define BUILDINGSPACING 20.
#define MAXBUILDINGINSET 12.
#define GALLERYHEIGHT 10.5
#define GALLERYINSET 2.5

#define SHOW_GALLERY
#define SHOW_LIGHTS
#define SHOW_BRIDGES
#define SHOW_MOON_AND_CLOUDS

float time;

// ===== Hash & Noise =====
float hash(float n){ return fract(sin(n)*32.5454412211233); }
vec2 hash2(float n){ return fract(sin(vec2(n,n+1.0))*vec2(11.1451239123,34.349430423)); }
vec3 hash3(float n){ return fract(sin(vec3(n,n+1.0,n+2.0))*vec3(84.54531253,42.145259123,23.349041223)); }

float noise(in vec2 x){
    vec2 p=floor(x);
    vec2 f=fract(x);
    vec2 uv=p.xy+f.xy*f.xy*(3.0-2.0*f.xy);
    return -1.0+2.0*textureLod(uChannel0,(uv+0.5)/256.0,0.0).x;
}

float noise(in vec3 x){
    float z=x.z*64.0;
    vec2 offz=vec2(0.317,0.123);
    vec2 uv1=x.xy+offz*floor(z);
    vec2 uv2=uv1+offz;
    return mix(texture(uChannel0,uv1,-100.0).x,texture(uChannel0,uv2,-100.0).x,fract(z))-0.5;
}

// ===== FBM =====
const mat3 m3=mat3(0.00,0.80,0.60,-0.80,0.36,-0.48,-0.60,-0.48,0.64);
float fbm(vec3 p){
    float f=0.0;
    f+=0.5000*noise(p); p=m3*p*2.02;
    f+=0.2500*noise(p); p=m3*p*2.03;
    f+=0.1250*noise(p); p=m3*p*2.01;
    f+=0.0625*noise(p);
    return f/0.9375;
}

// ===== Distance functions =====
float sdBox(vec3 p,vec3 b){ vec3 d=abs(p)-b; return min(max(d.x,max(d.y,d.z)),0.0)+length(max(d,0.0)); }
float sdSphere(vec3 p,float s){ return length(p)-s; }
float udBox(vec3 p,vec3 b){ return length(max(abs(p)-b,0.0)); }
float sdCylinderXY(vec3 p,vec2 h){ return length(p.xy)-h.x; } //max( length(p.xy)-h.x, abs(p.z)-h.y );
float sdCylinderXZ(vec3 p,vec2 h){ return max(length(p.xz)-h.x,abs(p.y)-h.y); }
float sdTriPrism(vec3 p,vec2 h){ vec3 q=abs(p); return max(q.z-h.y,max(q.x*0.866025+p.y*0.5,-p.y)-h.x*0.5); }

// ===== Combine ops =====
float opS(float d1,float d2){ return max(-d2,d1); }
float opU(float d1,float d2){ return min(d2,d1); }
vec2 opU(vec2 d1,vec2 d2){ return (d1.x<d2.x)?d1:d2; }
float opI(float d1,float d2){ return max(d1,d2); }

// ===== Building helpers =====
float getXoffset(float z){ return 20.*sin(z*0.02); }

vec2 getBuildingInfo(in vec3 pos){
    vec2 res;
    res.x=floor(pos.z/BUILDINGSPACING+0.5); // base index
    res.y=res.x*BUILDINGSPACING;            // base z coord
    res.x*=sign(pos.x+getXoffset(pos.z));   // negative index right side
    return res;
}

vec4 getBuildingParams(in float buildingindex){
    vec3 h=hash3(buildingindex);
    return vec4(
        20.+4.5*floor(h.x*7.),     // height
        h.y*MAXBUILDINGINSET,
        step(h.z,0.5),             // sidewalk
        step(abs(h.z-0.4),0.25)    // balcony
    );
}

float baseBuilding(in vec3 pos,in float h){
    vec3 tpos=vec3(pos.z,pos.y,pos.x);
    float res=opS(
        udBox(tpos,vec3(8.75,h,8.75)),
        opS(
            opU(
                sdBox(vec3(mod(tpos.x+1.75,3.5)-1.75,mod(tpos.y+4.5,9.)-2.5,tpos.z-5.),vec3(1.,2.,4.)),
                sdCylinderXY(vec3(mod(tpos.x+1.75,3.5)-1.75,mod(tpos.y+4.5,9.)-4.5,tpos.z-5.),vec2(1.,4.))
            ),
            udBox(tpos+vec3(0.,-h,0.),vec3(9.0,1.0,9.0))
        )
    );
    res=opU(
        res,
        opI(
            udBox(tpos,vec3(8.75,h,8.75)),
            opU(
                udBox(vec3(mod(tpos.x+1.75,3.5)-1.75,tpos.y,tpos.z-8.45),vec3(0.05,h,0.05)),
                udBox(vec3(tpos.x,mod(tpos.y+0.425,1.75)-0.875,tpos.z-8.45),vec3(10.0,0.05,0.05))
            )
        )
    );
    return res;
}

float baseGallery(in vec3 pos){
    vec3 tpos=vec3(pos.z,pos.y,pos.x);
    float res=opU(
        opS(
            udBox(tpos+vec3(0.,0.,-GALLERYINSET),vec3(8.75,GALLERYHEIGHT,0.125)),
            opU(
                sdBox(vec3(mod(tpos.x+1.75,3.5)-1.75,tpos.y-5.,tpos.z-5.),vec3(1.6,3.,10.)),
                sdCylinderXY(vec3(mod(tpos.x+1.75,3.5)-1.75,tpos.y-8.,tpos.z-5.),vec2(1.6,10.))
            )
        ),
        sdTriPrism(vec3(tpos.z+3.4,-44.4+3.9*tpos.y,tpos.x),vec2(7.5,8.7))
    );
    return res;
}

float baseBalcony(in vec3 pos,in float h){
    float res=opI(
        udBox(pos,vec3(9.0,h,9.0)),
        sdBox(vec3(pos.x,mod(pos.y+4.5,9.)-7.5,pos.z-5.),vec3(40.,0.5,40.))
    );
    return res;
}

float baseBridge(in vec3 pos){
    pos.x*=0.38;
    float res=opS(
        opU(
            sdBox(pos,vec3(4.,2.,2.5)),
            sdTriPrism(vec3(pos.x,-8.+3.*pos.y,pos.z),vec2(4.5,2.5))
        ),
        sdCylinderXY(pos+vec3(0.,1.5,0.),vec2(3.8,3.))
    );
    return res;
}

// ===== Distance fields =====
float mapSimpleTerrain(in vec3 p){
    p.x+=getXoffset(p.z);
    p.x=-abs(p.x);
    vec2 res=vec2(udBox(vec3(p.x+30.,p.y-1.,p.z),vec3(20.,100.25,99999.)),1.);
#ifdef SHOW_BRIDGES
    float zcenter=mod(p.z+60.,120.)-70.;
    res=opU(res,vec2(baseBridge(vec3(p.x,p.y,zcenter)),8.));
#endif
    return min(res.x,p.y+10.);
}

vec2 mapTerrain(in vec3 p){
    vec2 buildingInfo=getBuildingInfo(p);
    vec4 buildingParams=getBuildingParams(buildingInfo.x);

    vec3 pos=p;
    pos.x+=getXoffset(pos.z);
    pos.x=-abs(pos.x);

    vec2 res=vec2(udBox(vec3(pos.x+30.,pos.y,pos.z),vec3(20.,0.25,99999.)),1.); // ground

    float z=buildingInfo.y;
    float zcenter=mod(pos.z+10.,20.)-10.;

#ifdef SHOW_BRIDGES
    res=opU(res,vec2(baseBridge(vec3(pos.x,pos.y,mod(pos.z+60.,120.)-70.)),8.));
#endif

    res=opU(res,vec2(sdSphere(vec3(pos.x+11.5,pos.y-6.0,zcenter),0.5),3.));
    res=opU(res,vec2(sdSphere(vec3(pos.x+11.5,pos.y-5.4,zcenter+0.6),0.35),3.));
    res=opU(res,vec2(sdSphere(vec3(pos.x+11.5,pos.y-5.4,zcenter-0.6),0.35),3.));

    res=opU(res,vec2(sdCylinderXZ(vec3(pos.x+11.5,pos.y,zcenter),vec2(0.1,6.0)),4.));

    pos+=vec3(28.75+buildingParams.y,2.5,0.);
    res=opU(res,vec2(baseBuilding(vec3(pos.x,pos.y,zcenter),buildingParams.x+2.5),2.));

#ifdef SHOW_GALLERY
    pos.x+=-8.75-GALLERYINSET;
    res=mix(res,opU(res,vec2(baseGallery(vec3(pos.x,pos.y,zcenter)),5.)),buildingParams.z);
#endif

    return vec2(min(res.x,11.-zcenter),res.y);
}

float waterHeightMap(vec2 pos){
    const mat2 m2=mat2(0.80,-0.60,0.60,0.80);
    vec2 posm=0.02*pos*m2;
    posm.x+=0.001*time;
    float f=fbm(vec3(posm*1.9,time*0.01));
    float height=0.5+0.1*f;
    height+=0.05*sin(posm.x*6.0+10.0*f);
    return height;
}

// ===== Intersections =====
bool intersectPlane(vec3 ro,vec3 rd,float height,out float dist){
    if(rd.y==0.0) return false;
    float d=-(ro.y-height)/rd.y;
    d=min(100000.0,d);
    if(d>0.){ dist=d; return true; }
    return false;
}

bool intersectSphere(in vec3 ro,in vec3 rd,in vec4 sph,out vec3 normal){
    vec3 ds=ro-sph.xyz;
    float bs=dot(rd,ds);
    float cs=dot(ds,ds)-sph.w*sph.w;
    float ts=bs*bs-cs;
    if(ts>0.0){
        ts=-bs-sqrt(ts);
        if(ts>0.){ normal=normalize(((ro+ts*rd)-sph.xyz)/sph.w); return true; }
    }
    return false;
}

vec3 intersect(const vec3 ro,const vec3 rd){
    float maxd=1500.0;
    float precis=0.01;
    float h=precis*2.0;
    float t=0.0;
    float d=0.0;
    float m=1.0;
    for(int i=0;i<140;i++){
        if(abs(h)<precis || t>maxd) break; {
            t+=h;
            vec2 mt=mapTerrain(ro+rd*t);
            h=0.96*mt.x;
            m=mt.y;
        }
    }
    if(t>maxd) m=-1.0;
    return vec3(t,d,m);
}

float intersectSimple(const vec3 ro,const vec3 rd){
    float maxd=10000.0;
    float precis=0.01;
    float h=precis*2.0;
    float t=0.0;
    for(int i=0;i<50;i++){
        if(abs(h)<precis || t>maxd) break; {
            t+=h;
            h=mapSimpleTerrain(ro+rd*t);
        }
    }
    return t;
}

vec3 calcNormal(const vec3 pos){
    vec3 eps=vec3(0.1,0.0,0.0);
    return normalize(vec3(
        mapTerrain(pos+eps.xyy).x - mapTerrain(pos-eps.xyy).x,
        mapTerrain(pos+eps.yxy).x - mapTerrain(pos-eps.yxy).x,
        mapTerrain(pos+eps.yyx).x - mapTerrain(pos-eps.yyx).x ));
}

float calcAO(const vec3 pos,const vec3 nor){
    float totao=0.0;
    float sca=1.0;
    for(int aoi=0;aoi<5;aoi++){
        float hr=0.01+0.05*float(aoi);
        vec3 aopos=nor*hr+pos;
        float dd=mapTerrain(aopos).x;
        totao+=-(dd-hr)*sca;
        sca*=0.75;
    }
    return clamp(1.0-4.0*totao,0.0,1.0);
}

vec4 texcube(sampler2D sam,in vec3 p,in vec3 n){
    vec4 x=texture(sam,p.yz);
    vec4 y=texture(sam,p.zx);
    vec4 z=texture(sam,p.xy);
    return x*abs(n.x)+y*abs(n.y)+z*abs(n.z);
}

void getSkyColor(in vec3 rd,out vec3 bgcol,out vec3 col){
    vec3 lig=normalize(vec3(-2.5,1.7,2.5));
    bgcol=1.1*vec3(0.15,0.15,0.4)-rd.y*0.4;
    bgcol*=0.3;
    float moon=clamp(dot(rd,lig),0.0,1.0);
    bgcol+=vec3(2.0,1.5,0.8)*0.015*pow(moon,32.0);
    col=bgcol;
#ifdef SHOW_MOON_AND_CLOUDS
    vec3 normal;
    if(intersectSphere(vec3(0.,0.,0.),rd,vec4(lig,0.03),normal)){
        float l=dot(normalize(vec3(2.2,-1.9,0.5)),normal)*(0.4+texture(uChannel2,normal.xy*0.5).y);
        col+=0.2*clamp(2.5*vec3(2.0,1.5,0.8)*clamp(l,0.0,1.),vec3(0.),vec3(1.));
    }
    vec2 cuv=rd.xz*(100.0)/rd.y;
    float cc=texture(uChannel2,0.0001*cuv+0.1+0.0013*time).x;
    cc=0.65*cc+0.35*texture(uChannel2,0.0001*2.0*cuv+0.0013*.5*time).x;
    cc=smoothstep(0.3,1.0,1.1*cc);
    col=mix(col,0.1*vec3(0.05,0.05,0.4),0.99*cc);
#endif
}

// ===== Camera path =====
vec3 path(float _time){
    float z=_time*CAMERASPEED;
    return vec3(-getXoffset(z)+5.*cos(_time*0.1),1.25,z);
}

// ===== Main =====
void main(){
    time=uTime+43.;
    vec2 fragCoord=gl_FragCoord.xy;
    vec2 q=fragCoord/uResolution;
    vec2 p=-1.0+2.0*q;
    p.x*=uResolution.x/uResolution.y;

    
    vec3 ro=path(time);

    
    vec3 cw=vec3(0.0,0.0,1.0); // forward
    vec3 cu=vec3(1.0,0.0,0.0); // right
    vec3 cv=vec3(0.0,1.0,0.0); // up

    // yaw/pitch controls 
    float yaw  =(uMouse.z>0.0)?((uMouse.x/uResolution.x)-0.5)*1.5:0.0;
    float pitch=(uMouse.z>0.0)?((uMouse.y/uResolution.y)-0.5)*1.0:0.0;

   
    vec3 rd=normalize(p.x*cu+p.y*cv+2.1*cw);

    // rotati matrices
    mat3 rotYaw=mat3(
        cos(yaw),0.0,-sin(yaw),
        0.0,1.0,0.0,
        sin(yaw),0.0,cos(yaw)
    );
    mat3 rotPitch=mat3(
        1.0,0.0,0.0,
        0.0,cos(pitch),-sin(pitch),
        0.0,sin(pitch),cos(pitch)
    );

    // toepassen yaw en pitch
    rd=rotYaw*rotPitch*rd;

    //-----------------------------------------------------
    // render
    //-----------------------------------------------------
    float distSimple=intersectSimple(ro,rd);
    bool reflection=false;

    float dist,totaldist=0.,depth=0.;
    vec3 normal; vec3 tmat; vec3 lp; vec3 lig;

    vec3 col,bgcol;
    getSkyColor(rd,bgcol,col);

    if(intersectPlane(ro,rd,0.,dist) && dist<distSimple){
        ro=ro+rd*dist;
        totaldist=dist;

        depth=mapTerrain(ro).x;

        vec2 coord=ro.xz;
        vec2 dx=vec2(EPSILON,0.);
        vec2 dz=vec2(0.,EPSILON);

        float bumpfactor=BUMPFACTOR*(1.-smoothstep(0.,BUMPDISTANCE,dist));

        normal=vec3(0.,1.,0.);
        normal.x=-bumpfactor*(waterHeightMap(coord+dx)-waterHeightMap(coord-dx))/(2.*EPSILON);
        normal.z=-bumpfactor*(waterHeightMap(coord+dz)-waterHeightMap(coord-dz))/(2.*EPSILON);
        normal=normalize(normal);

        rd=reflect(rd,normal);
        reflection=true;
    }

    // intersect scene
    tmat=intersect(ro,rd);
    totaldist+=tmat.x;

    vec3 pos=ro+tmat.x*rd;

    if(tmat.z>-0.5 && totaldist<500.){
        // info building hit
        vec2 buildingInfo=getBuildingInfo(pos);
        vec4 buildingParams=getBuildingParams(buildingInfo.x);

        float z=buildingInfo.y;
        lp=vec3(11.5*sign(buildingInfo.x)-getXoffset(z),6.0,z);
        lig=normalize(lp-pos);

        // geometry
        vec3 nor=calcNormal(pos);

        // material
        vec3 mate,origmate;
        vec3 matpos=pos*0.3;

#ifdef SHOW_GALLERY
        if(tmat.z==5.)
            mate.xyz=texcube(uChannel3,matpos,nor).xyz*0.2;
        else
#endif
            origmate=mate.xyz=texcube(uChannel1,matpos,nor).xyz*0.4;

        bool aboveGallery=false;

        if(tmat.z==3.) mate.xyz=160.*vec3(1.30,1.10,0.40);
        else if(tmat.z==2.) mate.xyz*=clamp(4.*texture(uChannel2,buildingInfo.x*vec2(1.4231153121)).xyz,vec3(0.),vec3(1.));

        // lighting
        float occ=calcAO(pos,nor);
        float amb=clamp(0.5+0.5*nor.y,0.0,1.0);
        float dif=max(dot(nor,lig),0.0);
        if(tmat.z==5. && pos.y>GALLERYHEIGHT-2.6){
            dif=abs(dot(nor,lig));
            mate.xyz=vec3(0.3,0.,0.);
        }
        dif/=dot(lp-pos,lp-pos);

        float bac=max(0.2+0.8*dot(nor,normalize(vec3(-lig.x,0.0,-lig.z))),0.0);

        if(buildingParams.z==1. && pos.y>GALLERYHEIGHT){ aboveGallery=true; }
        vec3 lcol=aboveGallery?vec3(2.9,1.65,0.65):vec3(1.30,0.60,0.40);

        // lights
        vec3 brdf=vec3(0.0);
        brdf+=(60.0*dif)*lcol;
        brdf+=(0.1*amb)*vec3(0.10,0.15,0.30);
        brdf+=(0.1*bac)*vec3(0.09,0.03,0.01);

        // surface-light interaction
        col=(mate.xyz*brdf)*occ;

        // in room ?
        float isLeft=sign(buildingInfo.x);
        if(((pos.x+getXoffset(pos.z))*isLeft>buildingParams.y+20.25 &&
            abs(pos.z-buildingInfo.y)<8.5 &&
            pos.y<buildingParams.x-0.5) || false){
            vec2 roomcoord=pos.zy;
            roomcoord.x=floor((roomcoord.x-buildingInfo.y+5.)/3.5)*3.5+
                        floor((buildingInfo.y+5.)/10.)*10.;
            roomcoord.y=floor(roomcoord.y/9.)*9.;

            if(noise(vec3(roomcoord*1.15321*isLeft,time*0.0005))>-0.1){
                vec3 rlc=vec3(
                    (buildingParams.y+3.+20.25)*isLeft-getXoffset(roomcoord.x-5.),
                    roomcoord.y+5.5,
                    roomcoord.x-5.);
                vec3 ld=rlc-pos;
                dif=max(dot(nor,normalize(ld)),0.0)/dot(ld,ld);
                col+=origmate*(dif*120.)*texture(uChannel2,roomcoord*0.1231).xyz;
            }
        }

#ifdef SHOW_LIGHTS
        // extra lights
        float basez=floor((pos.z)/2.)*2.-2.0;
        for(int i=0;i<3;i++){
            buildingInfo=getBuildingInfo(vec3(pos.x,pos.y,basez));
            if(abs(basez-buildingInfo.y)>8.75 || noise(buildingInfo)>0.15){
                basez+=2.;
                continue;
            }
            buildingParams=getBuildingParams(buildingInfo.x);
            vec3 rlc=vec3((buildingParams.y-1.+20.25)*isLeft-getXoffset(basez),
                          7.7-1.5*abs(sin(basez*0.3)),basez);
            vec3 ld=rlc-pos;
            dif=max(dot(nor,normalize(ld)),0.0)/dot(ld,ld);
            col+=mate.xyz*(dif*6.0)*texture(uChannel2,vec2(basez*time*0.0001)*0.1231).xyz;
            basez+=2.;
        }
#endif

        if(reflection){
            col=mix(bgcol,col,exp(-0.00000001*pow(totaldist-dist,3.0)));
            col*=0.9*vec3(0.8,0.9,1.)*(0.5+clamp(depth*2.,0.0,0.5));
            if(dist!=totaldist) totaldist=dist;
        }
        col=mix(bgcol,col,exp(-0.00000001*pow(totaldist,3.0)));
    }

    //-----------------------------------------------------
    // postprocessing
    //-----------------------------------------------------
    col=clamp(col,0.0,1.0);
    col=pow(clamp(col,0.0,1.0),vec3(0.45));

    vec2 q2=fragCoord/uResolution;
    col*=vec3(1.03,1.02,1.0);
    col*=0.5+0.5*pow(16.0*q2.x*q2.y*(1.0-q2.x)*(1.0-q2.y),0.1);

    FragColor=vec4(col,1.0);
}
